"""Table-driven tests for the OCR bill-text parser.

The parser feeds the bill form with money figures, so clean, warning, and
garbage cases are covered explicitly. OCR itself (Tesseract) is not exercised
here — parse_bill_text operates on plain text.
"""

from datetime import date
from pathlib import Path

import pytest

from app.models.bill import UtilityType
from app.services.ocr_extract import (
    extract_text_from_image,
    extract_text_from_pdf,
    normalize_text,
    ocr_enabled,
    parse_bill_text,
)

FIXTURES = Path(__file__).parent / "fixtures"

ELECTRICITY_EN = """
Nama Supply Company
Account No: 12345678
Billing Period: 01/06/2026 - 30/06/2026
Previous Reading: 45200
Current Reading: 48860
Consumption: 3660 kWh
Total Due: OMR 40.990
"""

WATER_AR_EASTERN_DIGITS = """
شركة نماء لخدمات المياه
فترة الفاتورة: ٠١/٠٥/٢٠٢٦ - ٣١/٠٥/٢٠٢٦
الاستهلاك: ١٦ م٣
المبلغ المستحق: ٤٠٫٠٠٠ ر.ع
"""

ELECTRICITY_COST_MISMATCH = """
Billing Period: 01/01/2026 - 31/01/2026
Consumption: 1000 kWh
Total Due: OMR 99.000
"""

GARBAGE = "lorem ipsum dolor sit amet 42"

# Real Muscat Electricity Distribution layout: month-name dates, a charges
# table (header row and value row on separate lines after OCR flattening), and
# an "ageing of balance" block whose column header literally reads "...Total"
# with a stray 90 (from "Above 90 Days") that must NOT be mistaken for the bill total.
MUSCAT_TABULAR = """
MUSCAT ELECTRICITY DISTRIBUTION
Electricity Bill [All Amount in Rial Omani]
Current Reading/Date  Previous Reading Date  Days  Units Consumed (kWh)
38018  12 Mar 2014  35786  11 Feb 2014  29  233
Electricity Charges
Type  Consumption  Rate  Charges  Current Month Dues
Domestic  233  0.0140  3.262  3.262
Ageing of Balance
Upto 30 days  31-60 Days  61-90 Days  Above 90 Days  Total
Previous Outstanding  Current Month Dues  Total Bill Amount
1.130  3.262  3.262
"""


def test_month_name_dates_dd_mon_yyyy():
    text = "Current Reading 12 Mar 2014\nPrevious Reading 11 Feb 2014\nConsumption: 233 kWh\nTotal Bill Amount 3.262"
    bill = parse_bill_text(text)
    assert bill.period_start == date(2014, 2, 11)
    assert bill.period_end == date(2014, 3, 12)


def test_month_name_dates_dash_separated():
    text = "Bill Date 30-Apr-2026\nDue 15-May-2026\nConsumption: 10 m3\nTotal Due: OMR 25.0"
    bill = parse_bill_text(text)
    assert bill.period_start == date(2026, 4, 30)
    assert bill.period_end == date(2026, 5, 15)


def test_consumption_read_from_row_below_header():
    # "Consumption" is a column header; its value sits on the next line
    text = "Type  Consumption  Rate  Charges\nDomestic  233  0.0140  3.262"
    bill = parse_bill_text(text)
    assert bill.consumption == pytest.approx(233)


def test_cost_ignores_ageing_days_header_row():
    # The ageing row "...Above 90 Days  Total" must not yield cost=90
    text = (
        "Upto 30 days  31-60 Days  61-90 Days  Above 90 Days  Total\n"
        "Total Bill Amount\n"
        "1.130  3.262  3.262\n"
        "Consumption: 233 kWh\nBilling Period: 11/02/2014 - 12/03/2014"
    )
    bill = parse_bill_text(text)
    assert bill.cost == pytest.approx(3.262)
    assert bill.cost != pytest.approx(90)


def test_muscat_tabular_bill_end_to_end():
    bill = parse_bill_text(MUSCAT_TABULAR)
    assert bill.utility_type == UtilityType.electricity
    assert bill.consumption == pytest.approx(233)
    assert bill.period_start == date(2014, 2, 11)
    assert bill.period_end == date(2014, 3, 12)
    assert bill.cost == pytest.approx(3.262)
    assert bill.cost != pytest.approx(90)


@pytest.mark.skipif(not ocr_enabled(), reason="Tesseract not installed")
def test_real_muscat_bill_image_full_pipeline():
    """Regression on the actual low-res (768x1024) Muscat bill: the upscaling
    step in extract_text_from_image is what lets Tesseract read the digits."""
    data = (FIXTURES / "muscat_electricity.webp").read_bytes()
    bill = parse_bill_text(extract_text_from_image(data))
    assert bill.utility_type == UtilityType.electricity
    assert bill.consumption == pytest.approx(233)
    assert bill.cost == pytest.approx(3.475)
    assert bill.period_start == date(2014, 2, 11)
    assert bill.period_end == date(2014, 3, 12)
    assert bill.confidence == "high"


def test_rate_anchored_consumption_when_labels_are_lost():
    # Nama-style charges row after extraction: charge, rate, consumption inline
    # with no adjacent "Consumption" label. 121 * 0.0250 == 3.025 anchors it.
    text = "Electricity Bill\n3.025   0.0250   121   18-Mar-26   19-Apr-26\nBilling Period: 04/05/2026 - 30/05/2026"
    bill = parse_bill_text(text)
    assert bill.consumption == pytest.approx(121)


def test_non_residential_bill_skips_residential_tariff_check():
    # Non-residential rate differs from the modelled residential slabs, so the
    # cross-check must not fire (it would false-flag every commercial bill).
    text = (
        "Electricity Bill\nNon Residential\n"
        "3.025   0.0250   121\nTotal Bill Amount 3.176\n"
        "Billing Period: 04/05/2026 - 30/05/2026"
    )
    bill = parse_bill_text(text)
    assert bill.consumption == pytest.approx(121)
    assert not any("tariff" in w.lower() for w in bill.warnings)


def test_real_nama_pdf_full_pipeline():
    """Regression on the actual Nama non-residential PDF: digital text layer,
    scrambled labels. Utility + period + consumption recover; cost is left for
    the user (no reliable anchor in this layout)."""
    data = (FIXTURES / "nama_electricity.pdf").read_bytes()
    bill = parse_bill_text(extract_text_from_pdf(data))
    assert bill.utility_type == UtilityType.electricity
    assert bill.consumption == pytest.approx(121)
    assert bill.cost == pytest.approx(3.176)  # charge-anchored: 121*0.0250*1.05
    assert bill.period_start == date(2026, 5, 4)
    assert bill.period_end == date(2026, 5, 30)


def test_charge_anchored_cost_matches_printed_total_not_estimate():
    # Only a *printed* figure is returned. Here charge=100*0.025=2.5, +5% VAT
    # =2.625 which is printed; a non-matching gross must fall through to None.
    hit = "Consumption 100 0.0250 2.500\nAmount 2.625\nElectricity"
    assert parse_bill_text(hit).cost == pytest.approx(2.625)
    miss = "Consumption 100 0.0250 2.500\nAmount 9.999\nElectricity"
    assert parse_bill_text(miss).cost is None


def test_normalize_eastern_arabic_digits_and_decimal():
    assert normalize_text("٠١/٠٥/٢٠٢٦ الاستهلاك ١٦ المبلغ ٤٠٫٥") == "01/05/2026 الاستهلاك 16 المبلغ 40.5"


def test_electricity_bill_english_clean():
    bill = parse_bill_text(ELECTRICITY_EN)
    assert bill.utility_type == UtilityType.electricity
    assert bill.consumption == pytest.approx(3660)
    assert bill.unit == "kWh"
    assert bill.cost == pytest.approx(40.99)
    assert bill.period_start == date(2026, 6, 1)
    assert bill.period_end == date(2026, 6, 30)
    # cost matches the June-2026 relief tariff (3660 * 0.014 * 0.80) -> cross-check passes
    assert bill.confidence == "high"


def test_water_bill_arabic_eastern_digits():
    bill = parse_bill_text(WATER_AR_EASTERN_DIGITS)
    assert bill.utility_type == UtilityType.water
    assert bill.consumption == pytest.approx(16)
    assert bill.cost == pytest.approx(40.0)
    assert bill.period_start == date(2026, 5, 1)
    assert bill.period_end == date(2026, 5, 31)
    assert bill.confidence == "high"


def test_consumption_not_confused_with_meter_readings():
    bill = parse_bill_text(ELECTRICITY_EN)
    # 45200 / 48860 are meter readings, not consumption
    assert bill.consumption == pytest.approx(3660)


def test_electricity_tariff_cross_check_flags_mismatch():
    # 1000 kWh in Jan 2026 should cost ~14 OMR; bill says 99 -> warning + downgrade
    bill = parse_bill_text(ELECTRICITY_COST_MISMATCH)
    assert bill.confidence == "medium"
    assert any("tariff" in w.lower() for w in bill.warnings)


def test_garbage_text_returns_low_confidence_draft():
    bill = parse_bill_text(GARBAGE)
    assert bill.confidence == "low"
    assert bill.utility_type is None
    assert bill.cost is None
    assert bill.period_start is None
    assert len(bill.warnings) >= 1


def test_dates_ordered_even_if_reversed_in_text():
    text = "Period: 30/06/2026 to 01/06/2026\nConsumption: 10 m3\nTotal: OMR 25.0"
    bill = parse_bill_text(text)
    assert bill.period_start == date(2026, 6, 1)
    assert bill.period_end == date(2026, 6, 30)


def test_missing_cost_flagged():
    text = "Billing Period: 01/06/2026 - 30/06/2026\nConsumption: 12 m3"
    bill = parse_bill_text(text)
    assert bill.cost is None
    assert bill.confidence == "low"
    assert any("cost" in w.lower() for w in bill.warnings)
