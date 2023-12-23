from datetime import datetime
from typing import List, Optional, Union

from pydantic import constr, validator

from quart_starter import enums

from .helpers import BaseModel, parse_list, remove_queryset
from .pagination import PageInfo, Pagination
from .query import Query
from .user import User


class PostBase(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=128)
    content: str


class PostIn(PostBase):
    status: Optional[enums.PostStatusEnum] = enums.PostStatusEnum.PENDING


class Post(BaseModel):
    id: int
    title: str
    content: str
    status: enums.PostStatusEnum
    created_at: datetime
    modified_at: datetime
    published_at: Optional[datetime]

    author_id: int
    author: Optional[User]

    _remove_queryset = validator("author", allow_reuse=True, pre=True)(remove_queryset)


class PostFilterField(enums.EnumStr):
    ID_IN = "id__in"
    STATUS = "_status"
    AUTHOR_ID = "author_id"


class PostFilter(BaseModel):
    field: PostFilterField
    value: Union[str, int, List[str], List[int]]


class PostSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    TITLE_ASC = "title"
    TITLE_DESC = "-title"
    CREATED_AT_ASC = "created_at"
    CREATED_AT_DESC = "-created_at"
    PUBLISHED_AT_ASC = "published_at"
    PUBLISHED_AT_DESC = "-published_at"


class PostResolve(enums.EnumStr):
    AUTHOR = "author"


class PostQuery(BaseModel, Query):
    filters: List[PostFilter] = []
    sorts: List[PostSort] = [PostSort.ID_ASC]
    resolves: Optional[List[PostResolve]] = []
    page_info: PageInfo


class PostQueryStringSort(enums.EnumStr):
    ID_ASC = "id"
    ID_DESC = "-id"
    TITLE_ASC = "title__id"
    TITLE_DESC = "-title__id"
    CREATED_AT_ASC = "created_at__id"
    CREATED_AT_DESC = "-created_at__-id"
    PUBLISHED_AT_ASC = "published_at__id"
    PUBLISHED_AT_DESC = "-published_at__-id"


class PostQueryString(BaseModel):
    sort: Optional[PostQueryStringSort] = PostQueryStringSort.PUBLISHED_AT_DESC
    id__in: Optional[List[int]] = None
    status: Optional[str] = None
    pp: Optional[int] = 10
    p: Optional[int] = 1
    resolves: Optional[List[PostResolve]] = []

    _parse_list = validator("id__in", "resolves", allow_reuse=True, pre=True)(
        parse_list
    )

    def to_query(self, resolves=None):
        filters = []
        if self.id__in:
            filters.append(PostFilter(field=PostFilterField.ID_IN, value=self.id__in))

        if self.status:
            filters.append(PostFilter(field=PostFilterField.STATUS, value=self.status))

        resolves = resolves or self.resolves
        sorts = self.sort.split("__")
        page_info = PageInfo(num_per_page=self.pp, current_page=self.p)
        return PostQuery(
            filters=filters, sorts=sorts, resolves=resolves, page_info=page_info
        )


class PostResultSet(BaseModel):
    pagination: Pagination
    posts: List[Post]
