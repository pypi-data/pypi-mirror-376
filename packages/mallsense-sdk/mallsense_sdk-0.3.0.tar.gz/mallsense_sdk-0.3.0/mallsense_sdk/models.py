"""SDK request models for Bills and related APIs."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field

BlankEnum = Literal['']

class CashierModule(BaseModel):
    model_config = dict(extra='forbid')
    token: Optional[str] = None
    tenant: int
    is_active: Optional[bool] = None
    connector_type: str
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class CheckResultStatusUpdate(BaseModel):
    model_config = dict(extra='forbid')
    project_location_ids: Optional[List[int]] = None
    status: CheckResultStatusUpdateStatusEnum

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

CheckResultStatusUpdateStatusEnum = Literal['active', 'solved', 'closed']

CommentTypeEnum = Literal['status_change', 'comment']

ConnectorTypesEnum = Literal['alsep', 'astral', 'beeline', 'demo', 'dodo', 'dsm', 'evotor', 'firstofd', 'firstofd_v2', 'iiko', 'kontur', 'kzsoapover1c', 'lightkassa', 'moysklad', 'nifi', 'ofdru', 'ofdru_v2', 'over_ftp', 'platforma', 'posterpos', 'progfisc', 'prosklad', 'pysimple', 'renta', 'taxcom', 'tenzor', 'tis24', 'webkassa', 'yarus', 'yarusarenda']

ConnectorTypesIsolatedEnum = Literal['alsep', 'astral', 'beeline', 'demo', 'dodo', 'dsm', 'evotor', 'firstofd', 'firstofd_v2', 'iiko', 'kontur', 'kzsoapover1c', 'lightkassa', 'moysklad', 'nifi', 'ofdru', 'ofdru_v2', 'over_ftp', 'platforma', 'posterpos', 'progfisc', 'prosklad', 'pysimple', 'renta', 'taxcom', 'tenzor', 'tis24', 'webkassa', 'yarus', 'yarusarenda']

class Extension(BaseModel):
    model_config = dict(extra='forbid')
    connector: int
    name: str
    version: str
    config: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

FileFormatEnum = Literal['CSV', 'CSV_HEADERS', 'JSON', 'XML', 'EXCEL_XLS', 'EXCEL_XLSX']

NullEnum = Literal[None]

class PatchedCashierModule(BaseModel):
    model_config = dict(extra='forbid')
    token: Optional[str] = None
    tenant: Optional[int] = None
    is_active: Optional[bool] = None
    connector_type: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedCheckResultStatusUpdate(BaseModel):
    model_config = dict(extra='forbid')
    project_location_ids: Optional[List[int]] = None
    status: Optional[CheckResultStatusUpdateStatusEnum] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedExtension(BaseModel):
    model_config = dict(extra='forbid')
    connector: Optional[int] = None
    name: Optional[str] = None
    version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedPointOfSaleUpdate(BaseModel):
    model_config = dict(extra='forbid')
    date_from: Optional[str] = None
    date_to: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedStatus2Tenant(BaseModel):
    model_config = dict(extra='forbid')
    tenant_id: Optional[int] = None
    tenant_status_id: Optional[int] = None
    assigned_at: Optional[str] = None
    user_id: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedTenantComment(BaseModel):
    model_config = dict(extra='forbid')
    tenant: Optional[Tenant] = None
    status2tenant: Optional[Status2Tenant] = None
    responsibility_zone: Optional[ResponsibilityZone] = None
    user_id: Optional[int] = None
    comment_type: Optional[CommentTypeEnum] = None
    assigned_at: Optional[str] = None
    message: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedalsepSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_address: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedastralSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    api_key: Optional[str] = None
    organization: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedbeelineSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    email: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    kkts: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatcheddemoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    source_tenant_id: Optional[int] = None
    coefficient: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatcheddodoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    country: Optional[str] = None
    city: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatcheddsmSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    project: Optional[str] = None
    cm_id: Optional[str] = None
    port: Optional[int] = None
    active_hash: Optional[bool] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedevotorSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedfirstofdSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    organisation: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedfirstofdV2Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    inn: Optional[str] = None
    token: Optional[str] = None
    place_id: Optional[str] = None
    machine_number: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchediikoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    service_host: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedkonturSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Patchedkzsoapover1cSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    service_host: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedlightkassaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    token_part1: Optional[str] = None
    token_part2: Optional[str] = None
    itn: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedmoyskladSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchednifiSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    port: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedofdruSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedofdruV2Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    kkts: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedoverFtpSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    host: Optional[str] = None
    port: Optional[int] = None
    login: Optional[str] = None
    password: Optional[str] = None
    file_format: Optional[FileFormatEnum] = None
    jq_path: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedplatformaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    user_id: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedposterposSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedprogfiscSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    kkms: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedproskladSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedpushApiSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    jq_path: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedpysimpleSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    alias: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedrentaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn_tenant: Optional[str] = None
    inn_project: Optional[str] = None
    kpp_project: Optional[str] = None
    place_id: Optional[str] = None
    address: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedtaxcomSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    agreement_number: Optional[str] = None
    place_id: Optional[str] = None
    kkts: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedtenzorSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    place_id: Optional[str] = None
    kktSalesPoint: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Patchedtis24Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedwebkassaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedyarusSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    place_id: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PatchedyarusarendaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: Optional[str] = None
    password: Optional[str] = None
    inn: Optional[str] = None
    name: Optional[str] = None
    place_id: Optional[str] = None
    machine_number: Optional[str] = None
    tenant: Optional[int] = None
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class ResponsibilityZone(BaseModel):
    model_config = dict(extra='forbid')
    name: str

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Status2Tenant(BaseModel):
    model_config = dict(extra='forbid')
    tenant_id: int
    tenant_status_id: int
    assigned_at: Optional[str] = None
    user_id: int

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

Status77aEnum = Literal['no_sale', 'tenant_maintenance', 'change_software', 'mall_responsibility']

class StatusPointOfSaleManualCreate(BaseModel):
    model_config = dict(extra='forbid')
    point_of_sale: int
    date: Optional[str] = None
    status: Optional[Union[Status77aEnum, BlankEnum, NullEnum]] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class TaskCreatorInput(BaseModel):
    model_config = dict(extra='forbid')
    date_from: str
    date_to: str
    project_location_ids: List[int]
    tenant_ids: Optional[List[int]] = None
    connector_ids: Optional[List[int]] = None
    connector_types: Optional[List[ConnectorTypesEnum]] = None
    connector_types_isolated: Optional[List[ConnectorTypesIsolatedEnum]] = None
    task_ids: Optional[List[int]] = None
    priority: Optional[int] = None
    safe_update: Optional[bool] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Tenant(BaseModel):
    model_config = dict(extra='forbid')
    project_location: int
    name: str
    marker: str
    is_active: bool

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class TenantComment(BaseModel):
    model_config = dict(extra='forbid')
    tenant: Tenant
    status2tenant: Status2Tenant
    responsibility_zone: ResponsibilityZone
    user_id: int
    comment_type: CommentTypeEnum
    assigned_at: Optional[str] = None
    message: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class AlsepSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    place_address: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class AstralSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    api_key: str
    organization: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class BeelineSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    email: str
    password: str
    inn: str
    kkts: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class DemoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    source_tenant_id: int
    coefficient: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class DodoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    country: str
    city: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class DsmSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    project: str
    cm_id: str
    port: Optional[int] = None
    active_hash: Optional[bool] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class EvotorSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class FirstofdSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    organisation: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class FirstofdV2Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    inn: str
    token: str
    place_id: str
    machine_number: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class IikoSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    service_host: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class KonturSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: str
    login: str
    password: str
    inn: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Kzsoapover1cSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    service_host: str
    login: str
    password: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class LightkassaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    token_part1: Optional[str] = None
    token_part2: Optional[str] = None
    itn: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class MoyskladSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class NifiSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    port: int
    config: Dict[str, Any]
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class OfdruSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    inn: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class OfdruV2Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: str
    kkts: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class OverFtpSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    host: str
    port: Optional[int] = None
    login: str
    password: str
    file_format: Optional[FileFormatEnum] = None
    jq_path: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PlatformaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    inn: str
    user_id: Optional[str] = None
    place_id: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PosterposSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class ProgfiscSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    kkms: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class ProskladSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PushApiSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: Optional[str] = None
    jq_path: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class PysimpleSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    alias: str
    config: Dict[str, Any]
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class RentaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    inn_tenant: str
    inn_project: str
    kpp_project: str
    place_id: str
    address: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class TaxcomSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: str
    login: str
    password: str
    agreement_number: str
    place_id: str
    kkts: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class TenzorSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    integrator_id: str
    login: str
    password: str
    inn: str
    place_id: str
    kktSalesPoint: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class Tis24Serializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class WebkassaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class YarusSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    token: str
    place_id: str
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

class YarusarendaSerializer(BaseModel):
    model_config = dict(extra='forbid')
    is_active: Optional[bool] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    legal_entity: Optional[str] = None
    tenant_inn: Optional[str] = None
    tenant_kpp: Optional[str] = None
    tenant_ogrn: Optional[str] = None
    tenant_bik: Optional[str] = None
    tenant_agreement_number: Optional[str] = None
    tenant_address: Optional[str] = None
    comment: Optional[str] = None
    load_time_utc: Optional[List[int]] = None
    priority: Optional[int] = None
    include_bill_items: Optional[bool] = None
    aggregate_daily: Optional[bool] = None
    login: str
    password: str
    inn: str
    name: Optional[str] = None
    place_id: str
    machine_number: Optional[str] = None
    tenant: int
    proxy: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

# Resolve forward references for all models
def _rebuild_models():
    ns = globals()
    for cls in list(BaseModel.__subclasses__()):
        try:
            cls.model_rebuild(_types_namespace=ns, force=True)
        except Exception:
            pass

_rebuild_models()
