from quart import Blueprint
from quart_auth import login_user
from quart_schema import validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, schemas
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
        if not user.auth_id:
            user = await actions.user.update_auth_id(id=user.id)

        login_user(AuthUser(user.auth_id))
        return user

    raise ActionError("invalid email or password", loc="password")


@blueprint.post("/signup/")
@validate_request(schemas.SignupModel)
@validate_response(schemas.User, 200)
@atomic()
async def signup(data: schemas.SignupModel) -> schemas.User:
    user = await actions.user.create(
        schemas.UserCreate(name=data.email, email=data.email, password=data.password),
    )

    login_user(AuthUser(user.auth_id))
    return user
