from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Connect to Database
app.config["SQLALCHEMY_DATABASE_URI"] ="postgresql+psycopg2://apr_stds:123456@localhost:5432/apr_db"

db = SQLAlchemy(app)

# Create a model of a table
class Product(db.Model):
    # Define the name of the table
    __tablename__ = "products"
    # Define the primary key
    id = db.column(db.Integer, primary_key=True)
    # Define other attributes
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

# CLI Commands - Custom
@app.cli.command("Create")
def create_tables():
    print("Create all the tables")