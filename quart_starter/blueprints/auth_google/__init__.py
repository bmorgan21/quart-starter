import os

import google.auth.transport.requests
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from quart import Blueprint, abort, current_app, redirect, request, session, url_for
from quart_auth import AuthUser, login_user
from quart_schema import hide

from quart_starter import actions, schemas

blueprint = Blueprint("google_auth", __name__, template_folder="templates")

# this is to set our environment to https because OAuth 2.0 only
# supports https environments
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

client_secrets_file = os.path.join("tmp", "client_secret.json")


def get_flow():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ],
        redirect_uri=(url_for(".callback", _external=True)),
    )

    return flow


@blueprint.route("/login")  # the page where the user can login
@hide
def login():
    flow = get_flow()
    (
        authorization_url,
        state,
    ) = flow.authorization_url()
    session["state"] = state
    session["next"] = request.args.get(
        "r", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"])
    )
    return redirect(authorization_url)


@blueprint.route("/callback")
@hide
async def callback():
    """
    this is the page that will handle the callback process
    meaning process after the authorization
    """
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,  # pylint: disable=protected-access
        request=token_request,
        audience=credentials._client_id,  # pylint: disable=protected-access
    )

    print("!! ", id_info)

    email = id_info.get("email")
    user = await actions.user.get(email=email)
    if not user:
        user = await actions.user.create(
            schemas.UserCreate(name=id_info["name"], email=id_info["email"])
        )
    else:
        user = await actions.user.update_auth_id(id=user.id)

    login_user(AuthUser(user.auth_id))
    return redirect(
        session.pop("next", url_for(current_app.config["AUTH_LOGIN_SUCCESS_ENDPOINT"]))
    )
