import base64
import hashlib
import uuid
from typing import List

import bcrypt
from tortoise.exceptions import IntegrityError

from quart_starter import models, schemas
from quart_starter.lib.error import ActionError


async def get_user(
    id: int = None,
    email: str = None,
    auth_id: str = None,
    resolves: List[schemas.UserResolve] = None,
) -> schemas.User:
    user = None
    if id:
        user = await models.User.get_or_none(id=id)
    elif email:
        user = await models.User.get_or_none(email=email)
    elif auth_id:
        user = await models.User.get_or_none(auth_id=auth_id)

    if user:
        if resolves:
            await user.fetch_related(*resolves)

        return schemas.User.model_validate(user)

    return None


async def get_users(query: schemas.UserQuery) -> schemas.UserResultSet:
    queryset, pagination = await query.queryset(models.User)

    return schemas.UserResultSet(
        pagination=pagination,
        users=[schemas.User.model_validate(user) for user in await queryset],
    )


async def create_user(data: schemas.UserIn) -> schemas.User:
    md5_hash = hashlib.md5(data.email.encode()).hexdigest()
    gravatar = f"https://www.gravatar.com/avatar/{md5_hash}"

    try:
        user = await models.User.create(
            auth_id=data.auth_id or str(uuid.uuid4()),
            name=data.name,
            email=data.email,
            picture=gravatar,
            role=data.role,
        )
    except IntegrityError as error:
        if str(error).startswith(
            'duplicate key value violates unique constraint "user_email_key"'
        ):
            raise ActionError("email already exists", loc=["email"]) from error
        raise

    if data.password:
        await set_password(user.id, data.password)

    return schemas.User.model_validate(user)


async def delete_user(id: int) -> None:
    user = await models.User.get(id=id)
    await user.delete()


async def update_user_auth_id(id: int) -> schemas.User:
    user = await models.User.get_or_none(id=id)
    user.auth_id = str(uuid.uuid4())
    await user.save()

    return schemas.User.model_validate(user)


async def set_password(id: int, password: str) -> None:
    user = await models.User.get_or_none(id=id)

    user.hashed_password = bcrypt.hashpw(
        base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()),
        bcrypt.gensalt(),
    )
    await user.save()


async def check_password(id: int, password: str) -> bool:
    user = await models.User.get_or_none(id=id)

    return user.hashed_password and bcrypt.checkpw(
        base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()),
        user.hashed_password,
    )
