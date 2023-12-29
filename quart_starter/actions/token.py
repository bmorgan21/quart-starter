import uuid
from typing import List

from tortoise.expressions import F

from quart_starter import enums, models, schemas
from quart_starter.lib.error import ActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    token: schemas.Token,
    user_id: int,
    user_role: enums.UserRole,
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == token.user_id:
            return True
        return False

    if permission == enums.Permission.UPDATE:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == token.user_id:
            return True
        return False

    if permission == enums.Permission.DELETE:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == token.user_id:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    id: int = None, auth_id: int = None, resolves: List[schemas.TokenResolve] = None
) -> schemas.Post:
    token = None
    if id:
        token = await models.Token.get(id=id)
    elif auth_id:
        token = await models.Token.get(auth_id=auth_id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if resolves:
        await token.fetch_related(*resolves)

    return schemas.Token.model_validate(token)


@handle_orm_errors
async def query(q: schemas.TokenQuery) -> schemas.TokenResultSet:
    queryset, pagination = await q.queryset(models.Token)

    return schemas.TokenResultSet(
        pagination=pagination,
        tokens=[schemas.Token.model_validate(token) for token in await queryset],
    )


@handle_orm_errors
async def create(user_id: int, data: schemas.TokenCreate) -> schemas.TokenCreateSuccess:
    token = await models.Token.create(
        type=data.type, name=data.name, auth_id=str(uuid.uuid4()), user_id=user_id
    )

    await token.save()

    return schemas.TokenCreateSuccess.model_validate(token)


@handle_orm_errors
async def delete(id: int) -> None:
    token = await models.Token.get(id=id)
    await token.delete()


@handle_orm_errors
async def update(id: int, data: schemas.TokenPatch) -> schemas.Post:
    token = await models.Token.get(id=id)

    conditional_set(token, "name", data.name)

    await token.save()

    return schemas.Token.model_validate(token)
