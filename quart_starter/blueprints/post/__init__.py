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


class MessageManager(object):
    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id

    async def __aenter__(self):
        await current_app.socket_manager.add_user_to_channel(
            self.channel_id, websocket._get_current_object()
        )

        await self.send_message(
            "connected",
            f"User {self.user_id} connected to room - {self.channel_id}",
            data={
                "id": self.user_id,
                "name": await current_user.name,
                "picture": str(await current_user.picture),
                "session_id": get_session_id(self.user_id),
            },
        )

    async def __aexit__(self, exc_type, exc_val, traceback):
        if isinstance(exc_val, asyncio.CancelledError):
            await current_app.socket_manager.remove_user_from_channel(
                self.channel_id, websocket._get_current_object()
            )

            await self.send_message(
                "disconnected",
                f"User {self.user_id} disconnected from channel - {self.channel_id}",
                data={
                    "session_id": get_session_id(self.user_id),
                },
            )

    def __await__(self):
        return self.__aenter__().__await__()

    async def send_message(self, msg_type: str, message: str, data: Any = None):
        message = {
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "message": message,
            "type": msg_type,
        }

        if data is not None:
            message["data"] = data

        await current_app.socket_manager.broadcast_to_channel(
            self.channel_id, json.dumps(message)
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

    user_id = await current_user.id
    user_role = await current_user.role

    if not actions.post.has_permission(post, user_id, user_role, enums.Permission.READ):
        raise Forbidden()

    await actions.post.update_viewed(id)
    post.viewed += 1  # make sure the user sees their view

    user_id = await current_user.id

    t = MessageManager(user_id, f"post-{id}")
    t.send_message("view", f"User {user_id} viewed page", post.viewed)

    can_edit = actions.post.has_permission(
        post, await current_user.id, await current_user.role, enums.Permission.UPDATE
    )

    return await render_template("post/view.html", post=post, can_edit=can_edit)


@blueprint.route("/create/")
@login_required
async def create():
    user_id = await current_user.id
    user_role = await current_user.role

    if not actions.post.has_permission(
        None, user_id, user_role, enums.Permission.CREATE
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

    user_id = await current_user.id
    user_role = await current_user.role

    if not actions.post.has_permission(
        post, user_id, user_role, enums.Permission.UPDATE
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
    user_role = await current_user.role

    if not actions.post.has_permission(post, user_id, user_role, enums.Permission.READ):
        raise Forbidden()

    async with MessageManager(user_id, f"post-{id}") as mm:
        while True:
            data = await websocket.receive()
            mm.send_message("message", data)
