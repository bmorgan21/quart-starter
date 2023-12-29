from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden

blueprint = Blueprint("user", __name__)


@blueprint.post("/")
@validate_request(schemas.UserCreate)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def create(data: schemas.UserCreate) -> schemas.User:
    return await actions.user.create(data)


@blueprint.patch("/<int:id>/")
@validate_request(schemas.UserPatch)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.UserPatch) -> schemas.User:
    user = await actions.user.get(id=id)

    if not actions.user.has_permission(
        user, await current_user.id, await current_user.role, enums.Permission.UPDATE
    ):
        raise Forbidden()

    return await actions.user.update(id, data)
