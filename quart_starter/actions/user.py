import base64
import hashlib
import uuid
from typing import List

import bcrypt

from quart_starter import enums, models, schemas
from quart_starter.lib.error import ActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    user: schemas.User,
    user_id: int,
    user_role: enums.UserRole,
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user_role == enums.UserRole.ADMIN:
            return True
        return user_id == user.id

    if permission == enums.Permission.UPDATE:
        if user_role == enums.UserRole.ADMIN:
            return True
        return user_id == user.id

    if permission == enums.Permission.DELETE:
        if user_role == enums.UserRole.ADMIN:
            return True

    return False


@handle_orm_errors
async def get(
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
async def query(query: schemas.UserQuery) -> schemas.UserResultSet:
    queryset, pagination = await query.queryset(models.User)

    return schemas.UserResultSet(
        pagination=pagination,
        users=[schemas.User.model_validate(user) for user in await queryset],
    )


@handle_orm_errors
async def create(data: schemas.UserCreate) -> schemas.User:
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
async def delete(id: int) -> None:
    user = await models.User.get(id=id)
    await user.delete()


@handle_orm_errors
async def update(id: int, data: schemas.UserPatch) -> schemas.User:
    user = await models.User.get(id=id)

    conditional_set(user, "name", data.name)
    conditional_set(user, "email", data.email)
    conditional_set(user, "picture", data.picture)

    await user.save()

    return schemas.User.model_validate(user)


@handle_orm_errors
async def update_auth_id(id: int) -> schemas.User:
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
