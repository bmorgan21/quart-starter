from typing import List

from .helpers import PydanticBaseModel


class Error(PydanticBaseModel):
    loc: List[str]
    msg: str
    type: str


class Errors(PydanticBaseModel):
    errors: List[Error]
