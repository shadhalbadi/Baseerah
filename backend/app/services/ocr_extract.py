"""OCR bill extraction: image/PDF -> raw text -> draft bill.

Two deliberately separate stages:
  1. Text acquisition — Tesseract (eng+ara) for photos, pypdf's text layer for
     digital PDFs. Thin wrappers, not unit-tested.
  2. `parse_bill_text` — deterministic, rule-based field extraction. All the
     money-adjacent logic lives here and is table-tested.

OCR misreads digits silently, so the parser cross-checks electricity costs
against the tariff engine and the result is always a *draft* the user confirms
in the bill form — nothing is saved without review.
"""

import io
import os
import re
from datetime import date
from pathlib import Path

from app.config import get_settings
from app.models.bill import UtilityType
from app.schemas.extract import ExtractedBill
from app.services.tariff import electricity_cost

_EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

ELECTRICITY_KEYWORDS = ("kwh", "electricity", "كهرباء", "ك.و.س")
WATER_KEYWORDS = ("m3", "m³", "م3", "مياه", "water")
# "consumption" labels the charges table (value-first row); the generic
# "consumed" header sits above a meter-reading row where the consumption is the
# rightmost column — so the two tiers read their value differently.
CONSUMPTION_KEYWORDS = ("consumption", "الاستهلاك")
CONSUMED_KEYWORDS = ("consumed", "units consumed")
# Specific total labels are tried before the bare "total" fallback, so a stray
# "total" in a column header (e.g. the ageing-of-balance block) doesn't win.
STRONG_COST_KEYWORDS = (
    "total bill amount",
    "total amount",
    "amount due",
    "total due",
    "المبلغ المستحق",
    "الإجمالي المستحق",
)
COST_KEYWORDS = ("total", "المبلغ", "الإجمالي", "المستحق")

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b|\b(\d{4})-(\d{2})-(\d{2})\b")
# dd Mon yyyy / dd-Mon-yyyy — the format on Omani utility bills (e.g. 12 Mar 2014)
_MON_DATE_RE = re.compile(r"\b(\d{1,2})[ -]([A-Za-z]{3,9})[ -](\d{4})\b")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
TARIFF_TOLERANCE = 0.15


def normalize_text(text: str) -> str:
    """Western digits, '.' decimals, no Arabic thousands separators."""
    return text.translate(_EASTERN_DIGITS).replace("٫", ".").replace("٬", "")


def _strip_dates(line: str) -> str:
    return _MON_DATE_RE.sub(" ", _DATE_RE.sub(" ", line))


def _numbers(line: str) -> list[float]:
    cleaned = re.sub(r"(?<=\d),(?=\d{3}\b)", "", _strip_dates(line))
    return [float(m) for m in _NUMBER_RE.findall(cleaned)]


def _find_dates(text: str) -> list[date]:
    found = []
    for m in _DATE_RE.finditer(text):
        try:
            if m.group(1):  # dd/mm/yyyy
                found.append(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
            else:  # yyyy-mm-dd
                found.append(date(int(m.group(4)), int(m.group(5)), int(m.group(6))))
        except ValueError:
            continue
    for m in _MON_DATE_RE.finditer(text):  # dd Mon yyyy
        month = _MONTHS.get(m.group(2)[:3].lower())
        if month is None:
            continue
        year = int(m.group(3))
        if not 2000 <= year <= 2100:  # implausible year -> OCR misread
            continue
        try:
            found.append(date(year, month, int(m.group(1))))
        except ValueError:
            continue
    return found


def _detect_utility(text_lower: str) -> UtilityType | None:
    if any(k in text_lower for k in ELECTRICITY_KEYWORDS):
        return UtilityType.electricity
    if any(k in text_lower for k in WATER_KEYWORDS):
        return UtilityType.water
    return None


def _numbers_here_or_next(lines: list[str], i: int) -> list[float]:
    """Numbers on line i, or on the next non-empty line — OCR splits a table's
    column header and its values onto separate lines."""
    nums = _numbers(lines[i])
    if nums:
        return nums
    if i + 1 < len(lines):
        return _numbers(lines[i + 1])
    return []


def _find_consumption(lines: list[str]) -> float | None:
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in CONSUMPTION_KEYWORDS):
            nums = _numbers_here_or_next(lines, i)
            if nums:
                return nums[0]
    # "Units Consumed" heads a meter-reading row; consumption is the last column
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in CONSUMED_KEYWORDS):
            nums = _numbers_here_or_next(lines, i)
            if nums:
                return nums[-1]
    # fallback: a number immediately followed by a unit token
    for line in lines:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(kwh|m3|m³|م3)", line, re.IGNORECASE)
        if m:
            return float(m.group(1))
    # last resort: a charges row (Nama bills lose their English labels on
    # extraction) — an integer whose product with a per-kWh rate matches a
    # charge on the same line is the consumption. General across bill formats.
    return _rate_anchored_consumption(lines)


# Plausible OMR-per-kWh range for Omani residential/commercial tariffs.
_RATE_LO, _RATE_HI = 0.005, 0.2


def _rate_anchored_consumption(lines: list[str]) -> float | None:
    for line in lines:
        nums = _numbers(line)
        rates = [n for n in nums if _RATE_LO <= n <= _RATE_HI]
        ints = [n for n in nums if n.is_integer() and n >= 1]
        for rate in rates:
            for n in ints:
                if any(abs(n * rate - charge) < 0.02 for charge in nums):
                    return n
    return None


def _find_cost(lines: list[str], consumption: float | None = None) -> float | None:
    # An ageing-of-balance row ("...61-90 Days  Above 90 Days  Total") carries a
    # bare "total" and stray day counts — never a monetary total.
    def is_total_line(line: str) -> bool:
        return "day" not in line.lower()

    for keywords in (STRONG_COST_KEYWORDS, COST_KEYWORDS):
        for i, line in enumerate(lines):
            low = line.lower()
            if is_total_line(low) and any(k in low for k in keywords):
                nums = _numbers_here_or_next(lines, i)
                if nums:
                    return nums[-1]
    # fallback: a number adjacent to a currency token
    for line in lines:
        m = re.search(r"(?:omr|ر\.ع|\bro\b)\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:omr|ر\.ع|\bro\b)", line, re.IGNORECASE)
        if m:
            return float(m.group(1) or m.group(2))
    # last resort (labels lost, e.g. Nama PDFs): the current-month charge is
    # anchored by consumption*rate; the printed bill total is that charge plus
    # 5% Omani VAT. We only accept a *printed* VAT-inclusive figure — never the
    # bare charge — so we don't silently understate the amount due.
    return _charge_anchored_cost(lines, consumption)


OMAN_VAT = 0.05


def _charge_anchored_cost(lines: list[str], consumption: float | None) -> float | None:
    if consumption is None:
        return None
    all_nums = [n for line in lines for n in _numbers(line)]
    for line in lines:
        nums = _numbers(line)
        if consumption not in nums:
            continue
        for rate in (n for n in nums if _RATE_LO <= n <= _RATE_HI):
            charge = consumption * rate
            if not any(abs(charge - v) < 0.02 for v in nums):  # charge printed here?
                continue
            gross = charge * (1 + OMAN_VAT)
            match = min(all_nums, key=lambda v: abs(v - gross), default=None)
            if match is not None and abs(match - gross) < 0.02:
                return match
    return None


def parse_bill_text(text: str) -> ExtractedBill:
    norm = normalize_text(text)
    lines = [line.strip() for line in norm.splitlines() if line.strip()]
    lower = norm.lower()

    utility = _detect_utility(lower)
    consumption = _find_consumption(lines)
    cost = _find_cost(lines, consumption)
    dates = sorted(_find_dates(norm))
    period_start = dates[0] if dates else None
    period_end = dates[1] if len(dates) >= 2 else None

    warnings: list[str] = []
    if utility is None:
        warnings.append("Could not tell whether this is a water or electricity bill.")
    if consumption is None:
        warnings.append("Could not read the consumption figure.")
    if cost is None:
        warnings.append("Could not read the cost from the bill.")
    if period_start is None or period_end is None:
        warnings.append("Could not read the billing period dates.")

    complete = not warnings
    confidence = "high" if complete else "low"

    # Electricity figures can be validated against the APSR tariff — a mismatch
    # usually means OCR misread a digit (or the bill carries arrears/fees).
    # Only residential slabs are modelled, so skip the check for non-residential
    # accounts (their rate differs and the check would false-flag every bill).
    non_residential = any(k in lower for k in ("non residential", "non-residential", "commercial", "غير سكنية"))
    if complete and utility == UtilityType.electricity and not non_residential:
        expected = electricity_cost(consumption, year=period_start.year, month=period_start.month)
        if expected > 0 and abs(cost - expected) / expected > TARIFF_TOLERANCE:
            confidence = "medium"
            warnings.append(
                f"Cost ({cost}) does not match the tariff for {consumption} kWh "
                f"(~{round(expected, 2)}) — check for misread digits, arrears, or extra fees."
            )

    unit = None
    if utility == UtilityType.electricity:
        unit = "kWh"
    elif utility == UtilityType.water:
        unit = "m3"

    return ExtractedBill(
        utility_type=utility,
        period_start=period_start,
        period_end=period_end,
        consumption=consumption,
        unit=unit,
        cost=cost,
        confidence=confidence,
        warnings=warnings,
    )


# --- text acquisition -------------------------------------------------------


def _default_tessdata_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "tessdata"


def ocr_enabled() -> bool:
    return Path(get_settings().tesseract_cmd).exists()


# Phone photos and screenshots of a full bill leave individual digits far below
# the ~20px glyph height Tesseract needs, so it misreads them (233->203,
# 3.475->"3a75"). Upscaling toward this longest-edge target is the single
# biggest accuracy lever; PSM 6 then reads the bill as one uniform text block.
OCR_TARGET_MAX_DIM = 3000
OCR_MAX_UPSCALE = 4.0


def extract_text_from_image(data: bytes) -> str:
    import pytesseract
    from PIL import Image

    settings = get_settings()
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    tessdata = settings.tessdata_dir or str(_default_tessdata_dir())
    if Path(tessdata).exists():
        os.environ["TESSDATA_PREFIX"] = tessdata

    image = Image.open(io.BytesIO(data)).convert("L")
    scale = min(OCR_MAX_UPSCALE, max(1.0, OCR_TARGET_MAX_DIM / max(image.size)))
    if scale > 1.0:
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    return pytesseract.image_to_string(image, lang=settings.ocr_languages, config="--psm 6")


def extract_text_from_pdf(data: bytes) -> str:
    """Digital PDFs carry a text layer — no OCR needed. Scanned PDFs return ''.

    Plain mode keeps the English field labels (Electricity Bill, Units Consumed,
    KWH) needed for utility detection; layout mode drops them. The charge/rate/
    consumption row still lands on one line, which _rate_anchored_consumption uses.
    """
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
