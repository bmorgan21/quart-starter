from typing import List, Optional, Union

from pydantic import validator

from quart_starter import enums

from .helpers import BaseModel, parse_list
from .pagination import PageInfo, Pagination
from .query import Query


class UserBase(BaseModel):
    auth_id: Optional[str] = None
    name: str
    email: str
    status: Optional[str] = None
    picture: Optional[str] = None


class UserIn(UserBase):
    password: Optional[str] = None
    role: Optional[enums.UserRole] = enums.UserRole.USER


class User(UserBase):
    id: int
    role: enums.UserRole


class UserFilterField(enums.EnumStr):
    ID_IN = "id__in"


class UserFilter(BaseModel):
    field: UserFilterField
    value: Union[str, int, List[str], List[int]]


class UserSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    EMAIL_ASC = "email"
    EMAIL_DESC = "-email"
    NAME_ASC = "name"
    NAME_DESC = "-name"


class UserResolve(enums.EnumStr):
    pass


class UserQuery(BaseModel, Query):
    filters: List[UserFilter] = []
    sorts: List[UserSort] = [UserSort.ID_ASC]
    resolves: Optional[List[UserResolve]] = []
    page_info: PageInfo


class UserQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    EMAIL_ASC = "email__id"
    EMAIL_DESC = "-email__id"
    NAME_ASC = "name__id"
    NAME_DESC = "-name__id"


class UserQueryString(BaseModel):
    sort: Optional[UserQueryStringSort] = UserQueryStringSort.ID_ASC
    id__in: Optional[List[int]] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[UserResolve]] = []

    _parse_list = validator("id__in", "resolves", allow_reuse=True, pre=True)(
        parse_list
    )

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(UserFilter(field=UserFilterField.ID_IN, value=self.id__in))

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return UserQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class UserResultSet(BaseModel):
    pagination: Pagination
    users: List[User]
