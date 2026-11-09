# Importing every model here means Flask-Migrate can see all the tables.
from app.models.user import User
from app.models.product import Product
from app.models.job import Job, JobLine
from app.models.movement import StockMovement, MaterialRequest