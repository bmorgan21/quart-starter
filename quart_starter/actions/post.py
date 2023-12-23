from datetime import datetime
from typing import List

from quart_starter import models, schemas


async def get_post(
    id: int = None, resolves: List[schemas.PostResolve] = None
) -> schemas.Post:
    post = None
    if id:
        post = await models.Post.get_or_none(id=id)

    if post:
        if resolves:
            await post.fetch_related(*resolves)

        return schemas.Post.model_validate(post)

    return post


async def get_posts(
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


async def create_post(author_id: int, data: schemas.PostIn) -> schemas.Post:
    post = await models.Post.create(
        title=data.title, content=data.content, author_id=author_id
    )

    post.update_status(data.status)
    await post.save()

    return schemas.Post.model_validate(post)


async def delete_post(id: int) -> None:
    post = await models.Post.get(id=id)
    await post.delete()


async def update_post(id: int, data: schemas.PostIn) -> schemas.Post:
    post = await models.Post.get_or_none(id=id)

    if post:
        post.title = data.title
        post.content = data.content
        post.update_status(data.status)

        await post.save()

    return schemas.Post.model_validate(post)
