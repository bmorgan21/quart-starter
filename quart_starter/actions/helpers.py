import re
from functools import wraps
from inspect import iscoroutinefunction
from typing import Callable

from asyncpg.exceptions import UniqueViolationError
from tortoise.exceptions import DoesNotExist, IntegrityError

from quart_starter.lib.error import ActionError

unique_violation_detail_re = re.compile(
    r"Key \((?P<columns>.*?)\)=\((?P<values>.*?)\) already exists."
)


def handle_orm_errors(func: Callable) -> Callable:
    def handle_does_not_exist(error):
        raise ActionError("Entity Not Found", loc=[], type="NOT_FOUND") from error

    def handle_integrity_error(error):
        if isinstance(error.args[0], UniqueViolationError):
            m = unique_violation_detail_re.match(error.args[0].detail)

            if m:
                d = m.groupdict()
                raise ActionError(
                    f"{d['values']} already exists",
                    loc=[x.strip() for x in d["columns"].split(",")],
                    type="INTEGRITY",
                ) from error

        raise ActionError(str(error), loc=[], type="INTEGRITY")

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DoesNotExist as error:
            handle_does_not_exist(error)
        except IntegrityError as error:
            handle_integrity_error(error)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DoesNotExist as error:
            handle_does_not_exist(error)
        except IntegrityError as error:
            handle_integrity_error(error)

    return async_wrapper if iscoroutinefunction(func) else wrapper
