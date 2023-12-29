from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, schemas

blueprint = Blueprint("user", __name__)


@blueprint.post("/")
@validate_request(schemas.UserCreate)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def create(data: schemas.UserCreate) -> schemas.User:
    return await actions.user.create(await current_user.get_user(), data)


@blueprint.patch("/<int:id>/")
@validate_request(schemas.UserPatch)
@validate_response(schemas.User, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.UserPatch) -> schemas.User:
    return await actions.user.update(await current_user.get_user(), id, data)
