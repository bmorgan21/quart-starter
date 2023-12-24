from functools import wraps
from typing import Any, Callable

from quart import current_app
from quart_auth import AuthUser as _AuthUser
from quart_auth import current_user

from quart_starter import actions


class Unauthorized(Exception):
    pass


class Forbidden(Exception):
    pass


class AuthUser(_AuthUser):
    def __init__(self, auth_id):
        super().__init__(auth_id)
        self._resolved = False
        self._user = None

    async def _resolve(self):
        if not self._resolved:
            self._user = await actions.user.get(auth_id=self.auth_id)
            self._resolved = True

    async def __getattr__(self, name):
        await self._resolve()
        if self._user:
            return getattr(self._user, name)
        return None

    @property
    async def is_authenticated(self) -> bool:
        return await super().is_authenticated and await self.id

    async def has_roles(self, roles):
        return await self.is_authenticated and await self.role in roles


def login_required(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not await current_user.is_authenticated:
            raise Unauthorized()
        return await current_app.ensure_async(func)(*args, **kwargs)

    return wrapper


def roles_accepted(*role_names) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        async def decorator(*args: Any, **kwargs: Any) -> Any:
            if not await current_user.is_authenticated:
                raise Unauthorized()

            if not await current_user.has_roles(role_names):
                raise Forbidden()

            return await current_app.ensure_async(func)(*args, **kwargs)

        return decorator

    return wrapper
