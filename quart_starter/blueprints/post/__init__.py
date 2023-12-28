import asyncio
import json
from typing import Any

from quart import Blueprint, current_app, url_for, websocket
from quart.templating import render_template
from quart_auth import current_user, login_required
from quart_schema import validate_querystring

from quart_starter import actions, enums, schemas
from quart_starter.lib.auth import Forbidden
from quart_starter.lib.websocket import get_session_id

blueprint = Blueprint("post", __name__, template_folder="templates")


async def send_message(
    msg_type: str, user_id: str, channel_id: str, message: str, data: Any = None
):
    message = {
        "user_id": user_id,
        "channel_id": channel_id,
        "message": message,
        "type": msg_type,
    }

    if data is not None:
        message["data"] = data

    await current_app.socket_manager.broadcast_to_channel(
        channel_id, json.dumps(message)
    )


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

    user_id = await current_user.id

    await send_message(
        "view", user_id, f"post-{id}", f"User {user_id} viewed page", post.viewed
    )

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
async def update(id: int):
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


@blueprint.websocket("/<int:id>/ws")
@login_required
async def ws(id: int) -> None:
    post = await actions.post.get(id=id)

    user_id = await current_user.id

    if not actions.post.has_permission(
        post, user_id, await current_user.role, enums.Permission.READ
    ):
        raise Forbidden()

    channel_id = f"post-{id}"

    socket = websocket._get_current_object()  # pylint: disable=protected-access
    await current_app.socket_manager.add_user_to_channel(channel_id, socket)

    await send_message(
        "connected",
        user_id,
        channel_id,
        f"User {user_id} connected to room - {channel_id}",
        data={
            "id": user_id,
            "name": await current_user.name,
            "picture": str(await current_user.picture),
            "session_id": get_session_id(user_id),
        },
    )

    try:
        while True:
            data = await websocket.receive()
            message = {
                "user_id": user_id,
                "channel_id": channel_id,
                "message": data,
            }
            await current_app.socket_manager.broadcast_to_channel(
                channel_id, json.dumps(message)
            )

    except asyncio.CancelledError:
        await current_app.socket_manager.remove_user_from_channel(channel_id, socket)

        await send_message(
            "disconnected",
            user_id,
            channel_id,
            f"User {user_id} disconnected from channel - {channel_id}",
            data={
                "session_id": get_session_id(user_id),
            },
        )

        raise
