from datetime import date

from pydantic import BaseModel

from app.models.bill import UtilityType


class ExtractedBill(BaseModel):
    """Draft bill parsed from OCR text. Fields are nullable — the user reviews
    and completes them in the bill form; nothing is saved without confirmation."""

    utility_type: UtilityType | None
    period_start: date | None
    period_end: date | None
    consumption: float | None
    unit: str | None
    cost: float | None
    currency: str = "OMR"
    confidence: str  # high | medium | low
    warnings: list[str]


class ExtractionResult(BaseModel):
    enabled: bool  # false when the OCR engine is not installed on the server
    bill: ExtractedBill | None
    raw_text: str
