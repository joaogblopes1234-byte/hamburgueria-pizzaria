import sys
import os
sys.path.append(os.getcwd())
from app import app, db, User, Neighborhood, Order, OrderItem, Product
from datetime import datetime

with app.app_context():
    # Get first user, neighborhood and product
    user = User.query.first()
    neighborhood = Neighborhood.query.first()
    product = Product.query.first()

    if not user or not neighborhood or not product:
        print("Required data missing to create an order.")
    else:
        new_order = Order(
            user_id=user.id,
            address="Test Address",
            neighborhood_id=neighborhood.id,
            total_price=50.0,
            delivery_fee=7.0,
            status='Pending'
        )
        db.session.add(new_order)
        db.session.flush()

        item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=1,
            price_at_order=product.price
        )
        db.session.add(item)
        db.session.commit()
        print(f"Created order with ID: {new_order.id}")
