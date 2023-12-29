from typing import List, Union

from quart_starter import enums, models, schemas
from quart_starter.lib.error import ActionError, ForbiddenActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    user: schemas.User,
    obj: Union[schemas.User, None],
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user.role == enums.UserRole.ADMIN:
            return True
        return user.id == obj.id

    if permission == enums.Permission.UPDATE:
        if user.role == enums.UserRole.ADMIN:
            return True
        return user.id == obj.id

    if permission == enums.Permission.DELETE:
        if user.role == enums.UserRole.ADMIN:
            return True

    return False


@handle_orm_errors
async def get(
    user: schemas.User,
    id: int = None,
    email: str = None,
    auth_id: str = None,
    resolves: List[schemas.UserResolve] = None,
) -> schemas.User:
    obj = None
    if id:
        obj = await models.User.get(id=id)
    elif email:
        obj = await models.User.get(email=email)
    elif auth_id:
        obj = await models.User.get(auth_id=auth_id)
    else:
        raise ActionError("missing lookup key", type="not_found")

    if not has_permission(
        user, schemas.User.model_validate(obj), enums.Permission.READ
    ):
        raise ForbiddenActionError()

    if resolves:
        await obj.fetch_related(*resolves)

    return schemas.User.model_validate(obj)


@handle_orm_errors
async def query(user: schemas.User, q: schemas.UserQuery) -> schemas.UserResultSet:
    qs = models.User.all()
    if user.role != enums.UserRole.ADMIN:
        qs = qs.filter(id=user.id)

    queryset, pagination = await q.queryset(qs)

    return schemas.UserResultSet(
        pagination=pagination,
        users=[schemas.User.model_validate(user) for user in await queryset],
    )


@handle_orm_errors
async def create(user: schemas.User, data: schemas.UserCreate) -> schemas.User:
    if not has_permission(user, None, enums.Permission.CREATE):
        raise ForbiddenActionError()

    gravatar = data.picture or schemas.User.get_gravatar(data.email)

    obj = await models.User.create(
        name=data.name, email=data.email, picture=gravatar, role=enums.UserRole.USER
    )

    if data.password:
        obj.set_password(data.password)
        obj.save()

    return schemas.User.model_validate(obj)


@handle_orm_errors
async def delete(user: schemas.User, id: int) -> None:
    obj = await models.User.get(id=id)

    if not has_permission(
        user, schemas.User.model_validate(obj), enums.Permission.DELETE
    ):
        raise ForbiddenActionError()

    await obj.delete()


@handle_orm_errors
async def update(user: schemas.User, id: int, data: schemas.UserPatch) -> schemas.User:
    obj = await models.User.get(id=id)

    if not has_permission(
        user, schemas.User.model_validate(obj), enums.Permission.UPDATE
    ):
        raise ForbiddenActionError()

    conditional_set(obj, "name", data.name)
    conditional_set(obj, "email", data.email)
    conditional_set(obj, "picture", data.picture)

    await obj.save()

    return schemas.User.model_validate(obj)


@handle_orm_errors
async def check_password(id: int, password: str) -> bool:
    user = await models.User.get(id=id)

    return user.check_password(password)
