from datetime import datetime
from typing import List, Optional, Union

from pydantic import StringConstraints, field_validator
from typing_extensions import Annotated

from quart_starter import enums

from .helpers import NOTSET, BaseModel, parse_list
from .pagination import PageInfo, Pagination
from .query import Query

NAME_VALIDATOR = Annotated[str, StringConstraints(min_length=5)]
DATA_VALIDATOR = dict
STATUS_VALIDATOR = enums.EventStatus


class EventCreate(BaseModel):
    name: NAME_VALIDATOR
    data: DATA_VALIDATOR
    status: STATUS_VALIDATOR = enums.EventStatus.QUEUED


class EventPatch(BaseModel):
    status: STATUS_VALIDATOR = NOTSET
    num_attempts: int = NOTSET
    worker_id: Optional[str] = NOTSET
    next_attempt_at: datetime = NOTSET


class Event(BaseModel):
    id: int
    name: str
    data: dict
    status: str

    worker_id: Optional[str]
    num_attempts: int
    attempted_at: Optional[datetime]
    next_attempt_at: Optional[datetime]
    response_code: Optional[int]
    response_text: Optional[str]

    created_at: datetime
    modified_at: datetime


class EventFilterField(enums.EnumStr):
    ID_IN = "id__in"
    STATUS = "status"
    WORKER_ID = "worker_id"


class EventFilter(BaseModel):
    field: EventFilterField
    value: Union[str, int, List[str], List[int]]


class EventSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    NAME_ASC = "name"
    NAME_DESC = "-name"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"


class EventResolve(enums.EnumStr):
    pass


class EventGetOptions(BaseModel):
    resolves: Optional[List[EventResolve]] = []

    _parse_list = field_validator("resolves", mode="before")(parse_list)


class EventQuery(BaseModel, Query):
    filters: List[EventFilter] = []
    sorts: List[EventSort] = [EventSort.ID_ASC]
    resolves: Optional[List[EventResolve]] = []


class EventQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    NAME_ASC = "name__id"
    NAME_DESC = "-name__id"
    CREATED_AT_ASC = "created_at__id"
    CREATED_AT_DESC = "-created_at__-id"


class EventQueryString(BaseModel):
    sort: Optional[EventQueryStringSort] = EventQueryStringSort.CREATED_AT_DESC
    id__in: Optional[List[int]] = None
    status: Optional[enums.EventStatus] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[EventResolve]] = []

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(EventFilter(field=EventFilterField.ID_IN, value=self.id__in))

        if self.status:
            filters.append(
                EventFilter(field=EventFilterField.STATUS, value=self.status)
            )

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return EventQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class EventResultSet(BaseModel):
    pagination: Pagination
    events: List[Event]
