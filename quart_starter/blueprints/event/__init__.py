from quart import Blueprint, redirect, request, url_for
from quart.templating import render_template
from quart_auth import current_user
from quart_schema import validate_querystring

from quart_starter import actions, enums, schemas

blueprint = Blueprint("event", __name__, template_folder="templates")


@blueprint.route("/")
@validate_querystring(schemas.EventQueryString)
async def index(query_args: schemas.EventQueryString):
    if not query_args.status:
        return redirect(url_for(".index", status=enums.EventStatus.QUEUED))
    user = await current_user.get_user()
    resultset = await actions.event.query(user, query_args.to_query())

    subtab = query_args.status

    return await render_template(
        "event/index.html", resultset=resultset, tab="event", subtab=subtab
    )


@blueprint.post("/webhook")
async def webhook() -> str:
    data = await request.get_json()
    print("WEBHOOK POST DATA: ", data)
    return "OK"
