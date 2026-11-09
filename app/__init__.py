import os

from flask import Flask

from config import config
from app.extensions import db, migrate, login_manager
from app.errors import ApiError, register_error_handlers
from app.logging_setup import setup_logging


def create_app(config_name=None):
    """Build and return the Flask app. Tests can pass in 'testing'."""
    config_name = config_name or os.environ.get("APP_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # importing the models lets Flask-Migrate see every table
    from app import models  # noqa: F401
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def not_logged_in():
        raise ApiError("Please log in first.", 401)

    setup_logging(app)
    register_error_handlers(app)

    from app.blueprints import auth, inventory, jobs
    app.register_blueprint(auth.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(jobs.bp)

    return app