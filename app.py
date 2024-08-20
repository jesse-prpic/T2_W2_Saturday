from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta


app = Flask(__name__)

# Connect to Database                   (DMBS)      (DB_DRIVER) (DB USER)   (DB PASS) (URL)   (PORT)(DB_NAME)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://april_students:123456@localhost:5432/term2week2"
app.config["JWT_SECRET_KEY"] = "secret"

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

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

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "password", "is_admin")

users_schema = UserSchema(many=True, exclude=["password"])

user_schema = UserSchema(exclude=["password"])

@app.route("/auth/register", methods=["POST"])
def register_user():
    try:
        # Body of the request
        body_data = request.get_json()
        # Extracting the password from the body of the request
        password = body_data.get("password")
        # Hashing the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
        # Create a user using the User Model
        user = User(
            name = body_data.get("name"),
            email = body_data.get("email"),
            password = hashed_password    
        )
        # Add it to the db session
        db.session.add(user)
        # Commit
        db.session.commit()
        # Return something
        return user_schema.dump(user), 201
    except IntegrityError:
        return {"error": "Email adress already exists"}, 400
    
@app.route("/auth/login", methods=["POST"])
def login_user():
    # Find the user with the email
    body_data = request.get_json()
    # If the user exists and the password matches
    # SELECT * FROM user WHERE email = "user@gmail.com"
    stmt = db.select(User).filter_by(email=body_data.get("email"))
    user = db.session.scalar(stmt)
    # Create the jwt tocken
    if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
        token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        return {"token": token, "email": user.email, "is_admin": user.is_admin}
    else:
        return {"error": "Invalid email or password"}, 401
    # return the token

    # else
    # return an error message


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

    users = [
        User(
            name = "User 1",
            email = "user@email.com",
            password = bcrypt.generate_password_hash("123456").decode('utf8')
        ),
        User(
            email = "admin@gmail.com",
            password = bcrypt.generate_password_hash("abc123").decode('utf8'),
            is_admin = True
        )
    ]

    db.session.add_all(users)

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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
def delete_product(product_id):
    is_admin = authorisedAsAdmin()
    if not is_admin:
        return {"error": "Not authorized to delete a product"}, 403
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    if product:
        db.session.delete(product)
        db.session.commit()
        return {"message": f"Product with id {product_id} is successfully deleted"}
    else:
        return {"error": f"Product with id {product_id} doesn't exist"}, 404
    
def authorisedAsAdmin():
    # get the id of the user from the jwt token
    user_id = get_jwt_identity()
    # find the user in the db with the id
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    # check whether the user is an admin or not
    return user.is_admin