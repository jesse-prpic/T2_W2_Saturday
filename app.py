from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://april_students:123456@localhost:5432/term2week2"

db = SQLAlchemy(app)
ma = Marshmallow(app)

# create a Model of a table
class Product(db.Model):
    # Define the name of the table
    __tablename__ = "products"
    # Define the Primary Key
    id = db.Column(db.Integer, primary_key=True)
    # Define other attributes
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String)
    print = db.Column(db.Float)
    stock = db.Column(db.Integer)

# Creating a schema
class ProductSchema(ma.Schema):
    class Meta:
        # Fields
        fields = ("id", "name", "description", "print", "stock")

products_schema = ProductSchema(many=True)

product_schema = ProductSchema()

# CLI commands - Custom
@app.cli.command("create")
def create_tables():
   db.create_all()
   print("Create all the tables")

# Create another command to seed values to the table
@app.cli.command("seed")
def seed_tables():
    # Create a product object, tere is two ways
    # 1 
    product1= Product(
        name = "Fruits",
        description = "Fresh fruits",
        print = 5.99,
        stock = 100
    )
    # 2
    product2 = Product()
    product2.name = "Vegetables"
    product2.description = "Fresh Vegetables"
    product2.print = 10.99
    product2.stock = 200


    # Add to session
    db.session.add(product1)
    db.session.add(product2)

    # Commit
    db.session.commit()

    print("Table seeded")

# To drop the tables
@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped successfully")

# Working with routes
# define routes
@app.route("/products")
def get_products():

    stmt = db.select(Product)

    products_list = db.session.scalars(stmt)
    # Serialisation
    data = products_schema.dump(products_list)
    return data

@app.route("/products/<int:product_id>")
def get_product(product_id):
    stmt = db.select(Product).filter_by(id=product_id)

    product = db.session.scalar(stmt)
    if product:
        data = product_schema.dump(product)
        return data
    else:
        return{"error": f"Product with id {product_id} doesn't exist"}, 404
    
@app.route("/products", methods=["Post"])
def app_product():
    product_fields = request.get_json()

    new_product = Product(
        name = product_fields.get("name"),
        description = product_fields.get("description"),
        print = product_fields.get("print"),
        stock = product_fields.get("stock"),
    )

    db.session.add(new_product)
    db.session.commit()
    return product_schema.dump(new_product), 201

# UPDATE
@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):

    # Find the product from the database with the specific id, product_id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    # Retrieve the data from the body of the request
    body_data = request.get_json()
    # Update
    if product:
        product.name = body_data.get("name") or product.name
        product.description = body_data.get("description") or product.description
        product.print = body_data.get("print") or product.print
        product.stock = body_data.get("stock") or product.stock

        # Commit
        db.session.commit()
        return product_schema.dump(product)
    else:
        return {"error": f"Product with id{product_id} doesn't exist"}, 404
    
# DELETE
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    if product:
        db.session.delete(product)
        db.session.commit()
        return {"message": f"Product with id {product_id} is successfully deleted"}
    else:
        return {"error": f"Product with id {product_id} doesn't exist"}, 404