# The database object lives in its own file so every other file can import it
# without causing circular imports.
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()