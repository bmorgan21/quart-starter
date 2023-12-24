from quart import Blueprint
from quart_auth import current_user
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden, login_required

blueprint = Blueprint("post", __name__)


@blueprint.post("/")
@validate_request(schemas.PostIn)
@validate_response(schemas.Post, 200)
@atomic()
@login_required
async def create(data: schemas.PostIn) -> schemas.Post:
    if not actions.post_has_permission(
        None, await current_user.id, await current_user.role, enums.Permission.CREATE
    ):
        raise Forbidden()

    return await actions.create_post(await current_user.id, data)


@blueprint.put("/<int:id>/")
@validate_request(schemas.PostIn)
@validate_response(schemas.Post, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.PostIn) -> schemas.Post:
    post = await actions.get_post(id=id)

    if not actions.post_has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.UPDATE
    ):
        raise Forbidden()

    return await actions.update_post(id, data)


@blueprint.delete("/<int:id>/")
@validate_response(schemas.DeleteConfirmed, 200)
@atomic()
@login_required
async def delete(id: int) -> schemas.DeleteConfirmed:
    post = await actions.get_post(id=id)

    if not actions.post_has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.DELETE
    ):
        raise Forbidden()

    await actions.delete_post(id)

    return schemas.DeleteConfirmed(id=id)
