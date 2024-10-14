import signal
import time
import uuid

import click
from tortoise import Tortoise, run_async
from tortoise.transactions import in_transaction

from quart_starter import actions, enums, schemas, settings
from quart_starter.lib.delay_signals import DelaySignals


async def atomic_action(func, *args, **kwargs):
    await Tortoise.init(config=settings.TORTOISE_ORM)

    async with in_transaction():
        return await func(*args, **kwargs)


def register_commands(app):
    @app.cli.command("create-post", help="Create a Post with the given title")
    @click.argument("title")
    def _create_post(title):
        run_async(atomic_action(create_post, title))

    @app.cli.command("process-events", help="Send out webhook events")
    def _process_events():
        run_async(process_events())

    return app


async def create_post(title):
    system_user = await actions.user.system_user()
    post = await actions.post.create(
        system_user,
        schemas.PostCreate(
            title=title,
            content="some random content",
            status=enums.PostStatus.DRAFT,
        ),
    )

    print(f"Created Post: {post.title} (ID: {post.id})")


async def process_events():
    worker_id = str(uuid.uuid4())

    await Tortoise.init(config=settings.TORTOISE_ORM)

    system_user = await actions.user.system_user()

    WORKER_QUEUE_SIZE = 5

    while True:
        await actions.event.reset_abandoned(system_user)

        events = await actions.event.reserved_for_worker(system_user, worker_id)

        limit = max(0, WORKER_QUEUE_SIZE - len(events))

        if limit > 0:
            async with in_transaction():
                await actions.event.reserve_for_worker(
                    system_user, worker_id, limit=limit
                )

            events = await actions.event.reserved_for_worker(system_user, worker_id)

        print(f"Processing {len(events)} events")
        for event in events:
            with DelaySignals(signal.SIGINT, unless_repeated_n_times=5):
                try:
                    async with in_transaction():
                        await actions.event.worker_webhook(
                            system_user, event.id, worker_id
                        )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"ERROR: {e}, continuing")

        print("Sleeping...")
        time.sleep(5)
