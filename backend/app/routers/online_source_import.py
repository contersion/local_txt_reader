from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.legado_import import LegadoImportRequest, LegadoImportResult
from app.services.online.legado_importer import import_legado_source, validate_legado_import_payload
from app.services.online.online_sources import OnlineSourceError


router = APIRouter(prefix="/api/online-sources/import", tags=["online-sources-import"])


@router.post("/validate", response_model=LegadoImportResult)
def validate_legado_import(
    payload: LegadoImportRequest,
    current_user: CurrentUser,
) -> LegadoImportResult:
    _ = current_user
    return validate_legado_import_payload(payload)


@router.post("", response_model=LegadoImportResult, status_code=status.HTTP_201_CREATED)
def import_legado_source_endpoint(
    payload: LegadoImportRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        result = import_legado_source(db, current_user.id, payload)
    except OnlineSourceError as exc:
        failure = LegadoImportResult.model_validate(
            {
                "is_valid": False,
                "errors": [
                    {
                        "code": "LEGADO_MAPPING_FAILED",
                        "error_code": "LEGADO_MAPPING_FAILED",
                        "message": str(exc),
                        "severity": "error",
                        "source_path": None,
                        "stage": None,
                        "field_name": None,
                        "raw_value": None,
                        "normalized_value": None,
                    }
                ],
                "warnings": [],
                "ignored_fields": [],
                "unsupported_fields": [],
            }
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=failure.model_dump(mode="json"))

    if not result.is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=result.model_dump(mode="json"))
    return result
