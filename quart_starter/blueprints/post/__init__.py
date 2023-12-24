from quart import Blueprint
from quart.templating import render_template
from quart_auth import current_user
from quart_schema import validate_querystring

from quart_starter import actions, enums, schemas

blueprint = Blueprint("post", __name__, template_folder="templates")


@blueprint.route("/")
@validate_querystring(schemas.PostQueryString)
async def index(query_args: schemas.PostQueryString):
    resultset = await actions.post.query(
        query_args.to_query(resolves=["author"]),
        status=enums.PostStatus.PUBLISHED,
    )

    return await render_template(
        "post/index.html", resultset=resultset, tab="blog", subtab="all"
    )


@blueprint.route("/mine")
@validate_querystring(schemas.PostQueryString)
async def mine(query_args: schemas.PostQueryString):
    resultset = await actions.post.query(
        query_args.to_query(resolves=["author"]),
        author_id=await current_user.id,
    )

    return await render_template(
        "post/index.html",
        resultset=resultset,
        tab="blog",
        subtab="mine"
        if query_args.status == enums.PostStatus.PUBLISHED
        else "mine-pending",
    )


@blueprint.route("/<int:id>")
async def view(id: int):
    post = await actions.post.get(id=id, resolves=["author"])

    return await render_template("post/view.html", post=post)
