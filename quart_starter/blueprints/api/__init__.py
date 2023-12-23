from quart import Blueprint, url_for
from quart_auth import AuthUser, current_user, login_user
from quart_schema import tag, validate_querystring, validate_request, validate_response
from tortoise.transactions import atomic

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden, login_required
from quart_starter.lib.error import ActionError

blueprint = Blueprint("api", __name__, template_folder="templates")


@blueprint.post("/auth/login/")
@validate_request(schemas.LoginModel)
@validate_response(schemas.User, 200)
@validate_response(schemas.Errors, 400)
@tag(["auth"])
@atomic()
async def login(data: schemas.LoginModel) -> schemas.User:
    user = await actions.get_user(email=data.email)
    if user and await actions.check_password(user.id, data.password):
        if not user.auth_id:
            user = await actions.update_user_auth_id(id=user.id)

        login_user(AuthUser(user.auth_id))
        return user

    raise ActionError("invalid email or password", loc=["email", "password"])


@blueprint.post("/auth/signup/")
@validate_request(schemas.SignupModel)
@validate_response(schemas.User, 200)
@validate_response(schemas.Errors, 400)
@tag(["auth"])
@atomic()
async def signup(data: schemas.SignupModel) -> schemas.User:
    role = enums.UserRoleEnum.USER

    user = await actions.create_user(
        schemas.UserIn(
            name=data.email, email=data.email, password=data.password, role=role
        ),
    )

    login_user(AuthUser(user.auth_id))
    return user


def check_post_permission(post: schemas.Post, user):
    if user.role != enums.UserRoleEnum.ADMIN and post.author_id != user.id:
        raise Forbidden()


@blueprint.post("/post/")
@validate_request(schemas.PostIn)
@validate_response(schemas.Post, 200)
@validate_response(schemas.Errors, 400)
@tag(["post"])
@atomic()
@login_required
async def post_create(data: schemas.PostIn) -> schemas.Post:
    return await actions.create_post(await current_user.id, data)


@blueprint.put("/post/<int:id>/")
@validate_request(schemas.PostIn)
@validate_response(schemas.Post, 200)
@validate_response(schemas.Errors, 400)
@tag(["post"])
@atomic()
@login_required
async def post_update(id: int, data: schemas.PostIn) -> schemas.Post:
    post = await actions.get_post(id=id)

    check_post_permission(post, current_user)

    return await actions.update_post(id, data)


@blueprint.put("/post/<int:id>/")
@validate_response(schemas.DeleteConfirmed, 200)
@validate_response(schemas.Errors, 400)
@tag(["post"])
@atomic()
@login_required
async def post_delete(id: int) -> schemas.DeleteConfirmed:
    post = await actions.get_post(id=id)

    check_post_permission(post, current_user)

    await actions.delete_post(id)

    return schemas.DeleteConfirmed(id=id)
