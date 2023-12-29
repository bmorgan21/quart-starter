from quart import Blueprint, current_app
from quart_auth import current_user, login_required
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden

blueprint = Blueprint("token", __name__)


@blueprint.post("/")
@validate_request(schemas.TokenCreate)
@validate_response(schemas.TokenCreateSuccess, 200)
@atomic()
@login_required
async def create(data: schemas.TokenCreate) -> schemas.TokenCreateSuccess:
    if not actions.token.has_permission(
        None, await current_user.id, await current_user.role, enums.Permission.CREATE
    ):
        raise Forbidden()

    token = await actions.token.create(await current_user.id, enums.TokenType.API, data)

    token.auth_id = current_app.extensions["QUART_AUTH"][0].dump_token(token.auth_id)

    return token


@blueprint.patch("/<int:id>/")
@validate_request(schemas.TokenPatch)
@validate_response(schemas.Token, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.TokenPatch) -> schemas.Token:
    token = await actions.token.get(id=id)

    if not actions.token.has_permission(
        token, await current_user.id, await current_user.role, enums.Permission.UPDATE
    ):
        raise Forbidden()

    return await actions.token.update(id, data)
