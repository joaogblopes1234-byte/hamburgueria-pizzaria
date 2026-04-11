from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"{self.username} ({self.email})"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='products')
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return self.name

class Neighborhood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    delivery_fee = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"{self.name} (R$ {self.delivery_fee:.2f})"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending') # Pending, Preparing, Out for Delivery, Completed, Cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Alterado para nullable=True para checkout de visitante
    customer_name = db.Column(db.String(100), nullable=True) # Nome para visitante
    customer_phone = db.Column(db.String(20), nullable=True) # WhatsApp para visitante
    total_price = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    neighborhood_id = db.Column(db.Integer, db.ForeignKey('neighborhood.id'), nullable=False)
    neighborhood = db.relationship('Neighborhood', backref='orders')
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')
