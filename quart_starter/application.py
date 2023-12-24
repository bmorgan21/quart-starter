import datetime as dt
import urllib.parse

import humanize
import markdown
from markupsafe import Markup
from quart import Quart, redirect, request, url_for
from quart.templating import render_template
from quart_auth import QuartAuth
from quart_schema import QuartSchema
from quart_schema.validation import (
    RequestSchemaValidationError,
    ResponseSchemaValidationError,
)
from tortoise.contrib.quart import register_tortoise
from werkzeug.exceptions import NotFound

from quart_starter import schemas, settings
from quart_starter.command import register_commands
from quart_starter.lib.auth import AuthUser, Forbidden, Unauthorized
from quart_starter.lib.error import ActionError
from quart_starter.lib.middleware import ProxyMiddleware
from quart_starter.log import register_logging


def relative_url_for(**params):
    query_args = urllib.parse.parse_qs(request.query_string.decode("utf-8"))
    query_args.update(params)

    return url_for(request.url_rule.endpoint, **request.view_args, **query_args)


def utc_to_local(value):
    offset = None
    if "tz" in request.cookies:
        try:
            offset = int(request.cookies["tz"])
        except ValueError:
            offset = None

    if offset:
        return (value - dt.timedelta(seconds=offset)).replace(tzinfo=None)

    return value


def register_blueprints(app):
    # pylint: disable=import-outside-toplevel
    from quart_starter.blueprints.api import blueprint as api_blueprint
    from quart_starter.blueprints.auth import blueprint as auth_blueprint
    from quart_starter.blueprints.auth_google import blueprint as auth_google_blueprint
    from quart_starter.blueprints.marketing import blueprint as marketing_blueprint
    from quart_starter.blueprints.post import blueprint as post_blueprint

    # pylint: enable=import-outside-toplevel

    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(auth_google_blueprint, url_prefix="/auth/google")
    app.register_blueprint(marketing_blueprint)
    app.register_blueprint(post_blueprint, url_prefix="/post")


def create_app(**config_overrides):
    app = Quart(__name__, static_folder="static")
    app.asgi_app = ProxyMiddleware(app.asgi_app)

    QuartSchema(app)
    auth_manager = QuartAuth(app)
    auth_manager.user_class = AuthUser

    app.config.from_object(settings)
    app.config.update(config_overrides)

    register_logging(app)
    register_blueprints(app)
    register_tortoise(app, config=app.config["TORTOISE_ORM"])
    register_commands(app)

    # hide routes that don't have tags
    for rule in app.url_map.iter_rules():
        func = app.view_functions[rule.endpoint]

        if not rule.endpoint.startswith("api."):
            func.__dict__["_quart_schema_hidden"] = True
        else:
            tag = rule.endpoint.split(".")[1]
            setattr(func, "_quart_schema_tag", set([tag]))

            d = getattr(func, "_quart_schema_response_schemas")
            d[400] = (schemas.Errors, None)
            d[404] = (schemas.Error, None)

    @app.errorhandler(RequestSchemaValidationError)
    async def handle_request_validation_error(error):
        if error.validation_error:
            return (
                schemas.Errors(
                    errors=[
                        schemas.Error(
                            loc=x.get("loc"), type=x.get("type"), msg=x["msg"]
                        )
                        for x in error.validation_error.errors()
                    ]
                ),
                400,
            )
        return (
            schemas.Errors(
                errors=[schemas.Error(loc=[], type="VALIDATION", msg=str(error))]
            ),
            400,
        )

    @app.errorhandler(ResponseSchemaValidationError)
    async def handle_response_validation_error(error):
        if error.validation_error:
            return (
                schemas.Errors(
                    errors=[
                        schemas.Error(
                            loc=x.get("loc"), type=x.get("type"), msg=x["msg"]
                        )
                        for x in error.validation_error.errors()
                    ]
                ),
                400,
            )
        return (
            schemas.Errors(
                errors=[schemas.Error(loc=[], type="VALIDATION", msg=str(error))]
            ),
            400,
        )

    @app.errorhandler(ActionError)
    async def handle_field_value_error(error):
        if error.type == "NOT_FOUND":
            return schemas.Error(loc=[], type="NOT_FOUND", msg=str(error)), 404

        return (
            schemas.Errors(
                errors=[schemas.Error(loc=error.loc, type=error.type, msg=str(error))]
            ),
            400,
        )

    @app.errorhandler(Unauthorized)
    async def handle_response_unathorized_error(error):
        if request.accept_mimetypes.accept_html:
            return redirect(url_for("auth.login", r=request.url))

        return schemas.Error(loc=["auth_id"], type="UNAUTHORIZED", msg=str(error)), 401

    @app.errorhandler(Forbidden)
    async def handle_response_forbidden_error(error):
        if request.accept_mimetypes.accept_html:
            return await render_template("403.html")

        return schemas.Error(loc=["auth_id"], type="FORBIDDEN", msg=str(error)), 403

    @app.errorhandler(NotFound)
    async def handle_response_not_found_error(error):
        if request.accept_mimetypes.accept_html:
            return await render_template("404.html")

        return schemas.Error(loc=["page"], type="NOT_FOUND", msg=str(error)), 404

    @app.template_filter(name="ago")
    def ago_filter(value, default=""):
        if value:
            now = dt.datetime.now(dt.timezone.utc)
            delta = now - value
            if delta > dt.timedelta(days=1):
                value = utc_to_local(value)
                return value.strftime("%b %d, %Y")
            return humanize.naturaltime(delta)
        return default

    @app.template_filter(name="markdown")
    def markdown_filter(value):
        return Markup(markdown.markdown(value))

    @app.template_filter(name="format_datetime")
    def format_datetime(value, format="%m/%d/%Y %H:%M:%S"):
        value = utc_to_local(value)
        return value.strftime(format)

    @app.context_processor
    def add_context():
        return {"relative_url_for": relative_url_for}

    return app
