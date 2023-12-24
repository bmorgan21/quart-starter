import base64
import hashlib
import uuid
from typing import List

import bcrypt

from quart_starter import models, schemas
from quart_starter.lib.error import ActionError

from .helpers import handle_orm_errors


@handle_orm_errors
async def get_user(
    id: int = None,
    email: str = None,
    auth_id: str = None,
    resolves: List[schemas.UserResolve] = None,
) -> schemas.User:
    user = None
    if id:
        user = await models.User.get(id=id)
    elif email:
        user = await models.User.get(email=email)
    elif auth_id:
        user = await models.User.get(auth_id=auth_id)
    else:
        raise ActionError("missing lookup key", loc=[], type="NOT_FOUND")

    if resolves:
        await user.fetch_related(*resolves)

    return schemas.User.model_validate(user)


@handle_orm_errors
async def get_users(query: schemas.UserQuery) -> schemas.UserResultSet:
    queryset, pagination = await query.queryset(models.User)

    return schemas.UserResultSet(
        pagination=pagination,
        users=[schemas.User.model_validate(user) for user in await queryset],
    )


@handle_orm_errors
async def create_user(data: schemas.UserIn) -> schemas.User:
    md5_hash = hashlib.md5(data.email.encode()).hexdigest()
    gravatar = f"https://www.gravatar.com/avatar/{md5_hash}"

    user = await models.User.create(
        auth_id=data.auth_id or str(uuid.uuid4()),
        name=data.name,
        email=data.email,
        picture=gravatar,
        role=data.role,
    )

    if data.password:
        await set_password(user.id, data.password)

    return schemas.User.model_validate(user)


@handle_orm_errors
async def delete_user(id: int) -> None:
    user = await models.User.get(id=id)
    await user.delete()


@handle_orm_errors
async def update_user_auth_id(id: int) -> schemas.User:
    user = await models.User.get(id=id)
    user.auth_id = str(uuid.uuid4())
    await user.save()

    return schemas.User.model_validate(user)


@handle_orm_errors
async def set_password(id: int, password: str) -> None:
    user = await models.User.get(id=id)

    user.hashed_password = bcrypt.hashpw(
        base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()),
        bcrypt.gensalt(),
    )
    await user.save()


@handle_orm_errors
async def check_password(id: int, password: str) -> bool:
    user = await models.User.get(id=id)

    return user.hashed_password and bcrypt.checkpw(
        base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()),
        user.hashed_password,
    )
