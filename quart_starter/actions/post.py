from typing import List

from tortoise.expressions import F

from quart_starter import enums, models, schemas
from quart_starter.lib.error import ActionError

from .helpers import conditional_set, handle_orm_errors


def has_permission(
    post: schemas.Post,
    user_id: int,
    user_role: enums.UserRole,
    permission: enums.Permission,
) -> bool:
    if permission == enums.Permission.CREATE:
        return True

    if permission == enums.Permission.READ:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == post.author_id:
            return True
        return post.status == enums.PostStatus.PUBLISHED

    if permission == enums.Permission.UPDATE:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == post.author_id:
            return True
        return False

    if permission == enums.Permission.DELETE:
        if user_role == enums.UserRole.ADMIN:
            return True
        if user_id == post.author_id:
            return True
        return False

    return False


@handle_orm_errors
async def get(
    id: int = None, resolves: List[schemas.PostResolve] = None
) -> schemas.Post:
    post = None
    if id:
        post = await models.Post.get(id=id)
    else:
        raise ActionError("missing lookup key", loc=[], type="NOT_FOUND")

    if resolves:
        await post.fetch_related(*resolves)

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def query(
    query: schemas.PostQuery, status: str = None, author_id=None
) -> schemas.PostResultSet:
    qs = models.Post.all()
    if status:
        qs = qs.filter(_status=status)

    if author_id:
        qs = qs.filter(author_id=author_id)

    queryset, pagination = await query.queryset(qs)

    return schemas.PostResultSet(
        pagination=pagination,
        posts=[schemas.Post.model_validate(post) for post in await queryset],
    )


@handle_orm_errors
async def create(author_id: int, data: schemas.PostIn) -> schemas.Post:
    post = await models.Post.create(
        title=data.title, content=data.content, author_id=author_id
    )

    post.update_status(data.status)
    await post.save()

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def delete(id: int) -> None:
    post = await models.Post.get(id=id)
    await post.delete()


@handle_orm_errors
async def update(id: int, data: schemas.PostPatch) -> schemas.Post:
    post = await models.Post.get(id=id)

    conditional_set(post, "title", data.title)
    conditional_set(post, "content", data.content)

    if data.status != schemas.NOTSET:
        post.update_status(data.status)

    await post.save()

    return schemas.Post.model_validate(post)


@handle_orm_errors
async def update_viewed(id: int) -> None:
    await models.Post.filter(id=id).update(viewed=F("viewed") + 1)
