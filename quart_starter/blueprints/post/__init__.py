from quart import Blueprint, url_for
from quart.templating import render_template
from quart_auth import current_user, login_required
from quart_schema import validate_querystring

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden

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
@login_required
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

    if not actions.post.has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.READ
    ):
        raise Forbidden()

    await actions.post.update_viewed(id)
    post.viewed += 1  # make sure the user sees their view

    can_edit = actions.post.has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.UPDATE
    )

    return await render_template("post/view.html", post=post, can_edit=can_edit)


@blueprint.route("/create/")
@login_required
async def create():
    if not actions.post.has_permission(
        None, await current_user.id, await current_user.role, enums.Permission.CREATE
    ):
        raise Forbidden()

    return await render_template(
        "post/create.html",
        status_options=[(x.value.title(), x.value) for x in enums.PostStatus],
        r=url_for(".index"),
        tab="blog",
    )


@blueprint.route("/<int:id>/edit/")
@login_required
async def update(id):
    post = await actions.post.get(id=id)

    if not actions.post.has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.UPDATE
    ):
        raise Forbidden()

    return await render_template(
        "post/create.html",
        post=post,
        status_options=[(x.value.title(), x.value) for x in enums.PostStatus],
        r=url_for(".view", id=post.id),
        tab="blog",
    )
