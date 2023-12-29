from quart import Blueprint, current_app
from quart_auth import login_user
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import AuthUser
from quart_starter.lib.error import ActionError

blueprint = Blueprint("auth", __name__)


@blueprint.post("/token/")
@validate_request(schemas.AuthTokenCreate)
@validate_response(schemas.TokenCreateSuccess, 200)
@atomic()
async def token_create(data: schemas.AuthTokenCreate) -> schemas.TokenCreateSuccess:
    user = None
    try:
        user = await actions.user.get(email=data.email)
    except ActionError as error:
        if error.type != "action_error.does_not_exist":
            raise

    if user and await actions.user.check_password(user.id, data.password):
        token = await actions.token.create(
            user.id, enums.TokenType.WEB, schemas.TokenCreate(name="Web Login")
        )

        login_user(AuthUser(token.auth_id))

        token.auth_id = current_app.extensions["QUART_AUTH"][0].dump_token(
            token.auth_id
        )

        return token

    raise ActionError("invalid email or password", loc="password")


@blueprint.post("/user/")
@validate_request(schemas.AuthUserCreate)
@validate_response(schemas.User, 200)
@atomic()
async def user_create(data: schemas.AuthUserCreate) -> schemas.User:
    user = await actions.user.create(
        schemas.UserCreate(name=data.email, email=data.email, password=data.password),
    )

    token = await actions.token.create(
        user.id, enums.TokenType.WEB, schemas.TokenCreate(name="Web Login")
    )

    login_user(AuthUser(token.auth_id))
    return user
