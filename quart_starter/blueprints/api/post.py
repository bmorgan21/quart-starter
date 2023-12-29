from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, schemas

blueprint = Blueprint("post", __name__)


@blueprint.post("/")
@validate_request(schemas.PostCreate)
@validate_response(schemas.Post, 201)
@atomic()
@login_required
async def create(data: schemas.PostCreate) -> schemas.Post:
    return await actions.post.create(await current_user.get_user(), data), 201


@blueprint.patch("/<int:id>/")
@validate_request(schemas.PostPatch)
@validate_response(schemas.Post, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.PostPatch) -> schemas.Post:
    return await actions.post.update(await current_user.get_user(), id, data)


@blueprint.delete("/<int:id>/")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def delete(id: int) -> schemas.DeleteConfirmed:
    await actions.post.delete(await current_user.get_user(), id)

    return schemas.DeleteConfirmed(id=id)
