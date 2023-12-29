from quart import Blueprint
from quart_auth import login_user
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import AuthUser
from quart_starter.lib.error import ActionError

blueprint = Blueprint("auth", __name__)


@blueprint.post("/login/")
@validate_request(schemas.LoginModel)
@validate_response(schemas.User, 200)
@atomic()
async def login(data: schemas.LoginModel) -> schemas.User:
    user = None
    try:
        user = await actions.user.get(email=data.email)
    except ActionError as error:
        if error.type != "action_error.does_not_exist":
            raise

    if user and await actions.user.check_password(user.id, data.password):
        token = await actions.token.create(
            user.id, schemas.TokenCreate(type=enums.TokenType.WEB, name="Web Login")
        )

        login_user(AuthUser(token.auth_id))
        return user

    raise ActionError("invalid email or password", loc="password")
