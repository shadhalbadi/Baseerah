from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app import __version__

router = APIRouter(tags=["health"])


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
