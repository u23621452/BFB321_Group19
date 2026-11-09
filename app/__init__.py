import os

from flask import Flask

from config import config
from app.extensions import db, migrate


def create_app(config_name=None):
    """Build and return the Flask app. Tests can pass in 'testing'."""
    config_name = config_name or os.environ.get("APP_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # importing the models lets Flask-Migrate see every table
    from app import models  # noqa: F401

    return app