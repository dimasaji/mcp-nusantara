"""Human-confirmed official fields; technical provenance stays with the source."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetadataFact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)
    status: Literal['present', 'not_stated', 'unreadable']
    value: str | None = Field(default=None, min_length=1, max_length=1024)
    page_number: int | None = Field(default=None, ge=1)
    note: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def explicit_value_or_absence(self):
        if self.status == 'present' and not self.value:
            raise ValueError('Nilai metadata wajib diisi jika tercantum.')
        if self.status != 'present' and (self.value is not None or not self.note):
            raise ValueError('Metadata yang tidak tersedia memerlukan alasan dan nilai kosong.')
        return self


class SOPMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)
    schema_version: Literal[1] = 1
    logical_sop_id: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$')
    official_title: MetadataFact
    institution: MetadataFact
    unit: MetadataFact
    sop_number: MetadataFact
    jurisdiction: MetadataFact
    issued_on: MetadataFact
    effective_on: MetadataFact
    expires_on: MetadataFact
    revision: MetadataFact
    replaces_document_id: str | None = Field(default=None, min_length=1, max_length=256)
    validity: Literal['not_confirmed', 'confirmed_current', 'withdrawn', 'superseded']
    validity_note: str = Field(min_length=1, max_length=2000)

    @model_validator(mode='after')
    def official_fields(self):
        if self.official_title.status != 'present':
            raise ValueError('Judul resmi wajib diperiksa; nama file bukan judul terkonfirmasi.')
        for key in ('issued_on', 'effective_on', 'expires_on'):
            value = getattr(self, key).value
            if value and (len(value) != 10 or date.fromisoformat(value).isoformat() != value):
                raise ValueError('Tanggal metadata harus YYYY-MM-DD.')
        if self.effective_on.value and self.expires_on.value and self.expires_on.value < self.effective_on.value:
            raise ValueError('Tanggal akhir berlaku mendahului tanggal mulai berlaku.')
        return self

    def publication_allowed(self, today: date | None = None) -> bool:
        today = (today or date.today()).isoformat()
        return (self.validity not in {'withdrawn', 'superseded'}
                and (not self.effective_on.value or self.effective_on.value <= today)
                and (not self.expires_on.value or self.expires_on.value >= today))

    def facts(self):
        return {key: getattr(self, key) for key in (
            'official_title', 'institution', 'unit', 'sop_number', 'jurisdiction',
            'issued_on', 'effective_on', 'expires_on', 'revision')}
