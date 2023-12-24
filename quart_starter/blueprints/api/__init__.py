from quart import Blueprint

from .auth import blueprint as auth_blueprint
from .post import blueprint as post_blueprint

blueprint = Blueprint("api", __name__)

blueprint.register_blueprint(auth_blueprint, url_prefix="/auth")
blueprint.register_blueprint(post_blueprint, url_prefix="/post")
