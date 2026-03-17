from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel


class OnlineListSelector(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    parser: Literal["css", "jsonpath", "xpath", "regex"]
    expr: str = Field(min_length=1)


class OnlineFieldExtractor(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    parser: Literal["css", "jsonpath", "xpath", "regex"]
    expr: str = Field(min_length=1)
    attr: str | None = None
    trim: bool = True
    regex_group: int | None = Field(default=None, ge=0)
    join: str | None = None
    required: bool = False


class OnlineRequestDefinition(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    method: Literal["GET", "POST"]
    url: str = Field(min_length=1)
    response_type: Literal["html", "json"]
    headers: dict[str, str] = Field(default_factory=dict)
    query: dict[str, str] = Field(default_factory=dict)
    body: dict[str, str] = Field(default_factory=dict)


class OnlineStageDefinition(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    request: OnlineRequestDefinition
    list_selector: OnlineListSelector | None = None
    fields: dict[str, OnlineFieldExtractor] = Field(default_factory=dict)


class OnlineSourceDefinition(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    search: OnlineStageDefinition
    detail: OnlineStageDefinition
    catalog: OnlineStageDefinition
    content: OnlineStageDefinition


class OnlineSourceBase(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    enabled: bool = True
    base_url: str = Field(min_length=1, max_length=500)
    definition: OnlineSourceDefinition


class OnlineSourceCreate(OnlineSourceBase):
    pass


class OnlineSourceUpdate(OnlineSourceBase):
    pass


class OnlineSourceRead(ORMModel):
    id: int
    user_id: int
    name: str
    description: str | None = None
    enabled: bool
    base_url: str
    definition: OnlineSourceDefinition
    validation_status: Literal["unchecked", "valid", "invalid"]
    validation_errors: list[str] = Field(default_factory=list)
    last_checked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OnlineSourceValidateRequest(ORMModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    base_url: str = Field(min_length=1, max_length=500)
    definition: OnlineSourceDefinition


class OnlineSourceValidateResponse(ORMModel):
    is_valid: bool
    normalized_base_url: str
    normalized_definition: OnlineSourceDefinition
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OnlineSourceNormalizedPayload(ORMModel):
    normalized_base_url: str
    normalized_definition: dict[str, Any]
