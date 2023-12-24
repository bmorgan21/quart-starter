from pydantic import BaseModel as PydanticBaseModel
from tortoise.queryset import QuerySet


def remove_queryset(v):
    return None if isinstance(v, QuerySet) else v


def parse_list(v):
    return v.split(",") if isinstance(v, str) else v


class BaseModel(PydanticBaseModel):
    class Config:
        from_attributes = True


NOTSET = object()
