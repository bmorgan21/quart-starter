from quart import Blueprint, current_app, redirect, request, url_for
from quart.templating import render_template
from quart_auth import current_user, logout_user

from quart_starter import actions

blueprint = Blueprint(
    "auth", __name__, template_folder="templates", static_folder="static"
)


@blueprint.route("/login")
async def login():
    if await current_user.is_authenticated:
        return redirect(
            request.args.get(
                "r", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"])
            )
        )

    return await render_template(
        "auth/login.html",
        r=request.args.get(
            "r", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"])
        ),
    )


@blueprint.route("/logout")
async def logout():
    if await current_user.is_authenticated:
        await actions.token.delete(auth_id=current_user.auth_id)

    logout_user()
    return redirect(url_for(current_app.config["AUTH_LOGOUT_SUCCESS_ENDPOINT"]))


@blueprint.route("/signup")
async def signup():
    if await current_user.is_authenticated:
        return redirect(
            request.args.get(
                "r", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"])
            )
        )

    return await render_template(
        "auth/signup.html",
        r=request.args.get(
            "r", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"])
        ),
    )
