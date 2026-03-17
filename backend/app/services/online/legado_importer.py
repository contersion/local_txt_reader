from sqlalchemy.orm import Session

from app.schemas.legado_import import LegadoImportRequest, LegadoImportResult
from app.schemas.online_source import OnlineSourceCreate
from app.services.online.legado_mapper import map_legado_source
from app.services.online.legado_validator import LegadoValidationReport, validate_legado_source, validate_mapped_online_source
from app.services.online.online_sources import create_online_source
from app.services.online.source_normalizer import normalize_online_source_payload


def validate_legado_import_payload(payload: LegadoImportRequest) -> LegadoImportResult:
    report = validate_legado_source(payload.source)
    if not report.is_valid:
        return _build_result(report, mapped_source=None)

    mapped_source = map_legado_source(payload.source, report)

    if mapped_source is not None and report.is_valid:
        normalized_base_url, normalized_definition = normalize_online_source_payload(
            OnlineSourceCreate(
                name=mapped_source.name,
                description=mapped_source.description,
                enabled=mapped_source.enabled,
                base_url=mapped_source.base_url,
                definition=mapped_source.definition,
            )
        )
        validate_mapped_online_source(
            report,
            normalized_base_url=normalized_base_url,
            normalized_definition=normalized_definition,
        )
        if report.is_valid:
            mapped_source = type(mapped_source).model_validate(
                {
                    "name": mapped_source.name,
                    "description": mapped_source.description,
                    "enabled": mapped_source.enabled,
                    "base_url": normalized_base_url,
                    "definition": normalized_definition,
                }
            )

    return _build_result(report, mapped_source=mapped_source if report.is_valid else None)


def import_legado_source(
    db: Session,
    user_id: int,
    payload: LegadoImportRequest,
) -> LegadoImportResult:
    validation_result = validate_legado_import_payload(payload)
    if not validation_result.is_valid or validation_result.mapped_source is None:
        return validation_result

    created_source = create_online_source(
        db,
        user_id,
        OnlineSourceCreate(
            name=validation_result.mapped_source.name,
            description=validation_result.mapped_source.description,
            enabled=validation_result.mapped_source.enabled,
            base_url=validation_result.mapped_source.base_url,
            definition=validation_result.mapped_source.definition,
        ),
    )
    return validation_result.model_copy(update={"source_id": created_source.id})


def _build_result(
    report: LegadoValidationReport,
    *,
    mapped_source,
) -> LegadoImportResult:
    return LegadoImportResult.model_validate(
        {
            "is_valid": report.is_valid,
            "mapped_source": mapped_source,
            "errors": report.errors,
            "warnings": report.warnings,
            "ignored_fields": sorted(report.ignored_fields),
            "unsupported_fields": sorted(report.unsupported_fields),
        }
    )
