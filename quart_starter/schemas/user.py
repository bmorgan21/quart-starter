from typing import List, Optional, Union

from pydantic import HttpUrl, field_validator

from quart_starter import enums

from .helpers import NOTSET, BaseModel, EmailStr, PasswordStr, parse_list
from .pagination import PageInfo, Pagination
from .query import Query

ROLE_VALIDATOR = enums.UserRole
NAME_VALIDATOR = str
EMAIL_VALIDATOR = EmailStr
STATUS_VALIDATOR = enums.UserStatus
PICTURE_VALIDATOR = HttpUrl
PASSWORD_VALIDATOR = PasswordStr


class UserCreate(BaseModel):
    auth_id: Optional[str] = None
    name: NAME_VALIDATOR
    email: EMAIL_VALIDATOR
    status: STATUS_VALIDATOR = enums.UserStatus.PENDING
    picture: Optional[PICTURE_VALIDATOR] = None
    password: Optional[PASSWORD_VALIDATOR] = None
    role: ROLE_VALIDATOR = enums.UserRole.USER


class UserPatch(BaseModel):
    name: NAME_VALIDATOR = NOTSET
    email: EMAIL_VALIDATOR = NOTSET
    # Optional means the value can be None
    # https://docs.pydantic.dev/2.0/migration/#required-optional-and-nullable-fields
    picture: Optional[PICTURE_VALIDATOR] = NOTSET


class User(BaseModel):
    id: int
    auth_id: Optional[str]
    role: str
    name: str
    email: str
    status: str
    picture: Optional[PICTURE_VALIDATOR]


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

    _parse_list = field_validator("id__in", "resolves", mode="before")(parse_list)

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
