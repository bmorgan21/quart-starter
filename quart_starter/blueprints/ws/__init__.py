import asyncio
import json

from quart import Blueprint, current_app, redirect, request, url_for, websocket
from quart.templating import render_template
from quart_auth import current_user, login_required

from quart_starter import actions, enums
from quart_starter.lib.auth import Forbidden

blueprint = Blueprint("ws", __name__)


@blueprint.get("/index")
async def index():
    url = url_for("ws.ws")
    return """
    <script src="/static/js/websocket.js"></script>
<script type="text/javascript">


function onmessageCallback(message) {
    const li = document.createElement("li");
    li.appendChild(document.createTextNode(message));
    document.getElementById("messages").appendChild(li);
}

const WS = initWS('_URL_', onmessageCallback);

function send(event) {
    const message = (new FormData(event.target)).get("message");
    if (message) {
        WS.send(message);
    }
    event.target.reset();
    return false;
}
</script>

<div style="display: flex; height: 100%; flex-direction: column">
  <ul id="messages" style="flex-grow: 1; list-style-type: none"></ul>

  <form onsubmit="return send(event)">
    <input type="text" name="message" minlength="1" autofocus="autofocus"/>
    <button type="submit">Send</button>
  </form>
</div>
""".replace(
        "_URL_", url
    )


@blueprint.websocket("")
@login_required
async def ws() -> None:
    user_id = await current_user.id
    channel_id = "channel"

    socket_manager = current_app.socket_manager

    socket = websocket._get_current_object()  # pylint: disable=protected-access
    await socket_manager.add_user_to_channel(channel_id, socket)

    message = {
        "user_id": user_id,
        "channel_id": channel_id,
        "message": f"User {user_id} connected to room - {channel_id}",
    }
    await socket_manager.broadcast_to_channel(channel_id, json.dumps(message))

    try:
        while True:
            data = await websocket.receive()
            message = {
                "user_id": user_id,
                "channel_id": channel_id,
                "message": data,
            }
            await socket_manager.broadcast_to_channel(channel_id, json.dumps(message))

    except asyncio.CancelledError:
        await socket_manager.remove_user_from_channel(channel_id, socket)

        message = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message": f"User {user_id} disconnected from channel - {channel_id}",
        }
        await socket_manager.broadcast_to_channel(channel_id, json.dumps(message))

        raise
