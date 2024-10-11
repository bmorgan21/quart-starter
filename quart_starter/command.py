import click
from tortoise import Tortoise, run_async
from tortoise.transactions import in_transaction

from quart_starter import actions, enums, schemas, settings


async def atomic_action(func, *args, **kwargs):
    await Tortoise.init(config=settings.TORTOISE_ORM)

    async with in_transaction():
        return await func(*args, **kwargs)


def register_commands(app):
    @app.cli.command("create-post", help="Create a Post with the given title")
    @click.argument("title")
    def test_command(title):
        run_async(atomic_action(create_post, title))

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
