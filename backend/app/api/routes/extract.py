from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import OwnedProperty
from app.schemas.extract import ExtractionResult
from app.services.ocr_extract import (
    extract_text_from_image,
    extract_text_from_pdf,
    ocr_enabled,
    parse_bill_text,
)

router = APIRouter(prefix="/properties/{property_id}/bills/extract", tags=["extract"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("", response_model=ExtractionResult)
async def extract_bill(prop: OwnedProperty, file: UploadFile) -> ExtractionResult:
    if not ocr_enabled():
        return ExtractionResult(enabled=False, bill=None, raw_text="")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large (max 10 MB)")

    is_pdf = (file.content_type == "application/pdf") or (file.filename or "").lower().endswith(".pdf")
    try:
        text = extract_text_from_pdf(data) if is_pdf else extract_text_from_image(data)
    except Exception:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="could not read the file — upload a clear photo (JPEG/PNG) or a PDF bill",
        )

    if is_pdf and not text.strip():
        bill = parse_bill_text("")
        bill.warnings.insert(0, "This PDF has no text layer (scanned copy) — upload a photo of the bill instead.")
        return ExtractionResult(enabled=True, bill=bill, raw_text="")

    return ExtractionResult(enabled=True, bill=parse_bill_text(text), raw_text=text)
