from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Protocol, Tuple, Type, TypeVar
from uuid import UUID

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.sites.models import Site
from django.db.models import ForeignObjectRel, Model
from django.db.models.manager import BaseManager
from django.forms import Field

from edc_appointment.models import Appointment
from edc_metadata.metadata import Destroyer, Metadata
from edc_metadata.metadata_rules import MetadataRuleEvaluator
from edc_visit_schedule.schedule import Schedule, VisitCollection
from edc_visit_schedule.typing_stubs import VisitScheduleFieldsProtocol
from edc_visit_schedule.visit import Visit
from edc_visit_schedule.visit_schedule import VisitSchedule

_M = TypeVar("_M", bound=Model)
_Self = TypeVar("_Self", bound=Model)


class ModelBase(type):
    @property
    def objects(cls: type[_Self]) -> BaseManager[_Self]: ...  # noqa

    @property
    def _default_manager(cls: type[_Self]) -> BaseManager[_Self]: ...  # noqa

    @property
    def _base_manager(cls: type[_Self]) -> BaseManager[_Self]: ...  # noqa


class Options(Generic[_M]):
    def label_lower(self) -> str: ...  # noqa

    def fields(self) -> Tuple[Field]: ...  # noqa

    def get_fields(
        self, include_parents: bool = ..., include_hidden: bool = ...  # noqa
    ) -> list[Field | ForeignObjectRel | GenericForeignKey]: ...  # noqa


class SiteFieldsProtocol(Protocol):
    id: int
    name: str | None


class RelatedVisitProtocol(VisitScheduleFieldsProtocol, Protocol):
    metadata_cls: Type[Metadata]
    metadata_destroyer_cls: Type[Destroyer]
    metadata_rule_evaluator_cls: Type[MetadataRuleEvaluator]

    class Meta: ...  # noqa

    _meta: Options[Any]

    appointment: Appointment
    consent_version: str | None
    created: datetime | None
    id: UUID
    modified: datetime | None
    reason: str | None
    report_datetime: datetime | None
    schedule: Schedule
    site: Site
    subject_identifier: str | None
    user_created: str | None
    user_modified: str | None
    visit: Visit
    visit_schedule: VisitSchedule
    visits: VisitCollection
