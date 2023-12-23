from dataclasses import dataclass
from typing import List


@dataclass
class Error:
    loc: List[str]
    msg: str
    type: str


@dataclass
class Errors:
    errors: List[Error]
