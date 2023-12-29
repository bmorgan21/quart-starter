from quart import Blueprint, current_app
from quart_auth import current_user, login_required
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas

blueprint = Blueprint("token", __name__)


@blueprint.post("/")
@validate_request(schemas.TokenCreate)
@validate_response(schemas.TokenCreateSuccess, 200)
@atomic()
@login_required
async def create(data: schemas.TokenCreate) -> schemas.TokenCreateSuccess:
    user = await current_user.get_user()
    token = await actions.token.create(user, enums.TokenType.API, data)

    token.auth_id = current_app.extensions["QUART_AUTH"][0].dump_token(token.auth_id)

    return token


@blueprint.patch("/<int:id>/")
@validate_request(schemas.TokenPatch)
@validate_response(schemas.Token, 200)
@atomic()
@login_required
async def update(id: int, data: schemas.TokenPatch) -> schemas.Token:
    return await actions.token.update(await current_user.get_user(), id, data)
