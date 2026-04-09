from app import app
from models import db, Category, Product, User, Neighborhood
from werkzeug.security import generate_password_hash

def seed():
    with app.app_context():
        # Clear existing data if necessary (be careful in production!)
        db.drop_all()
        db.create_all()

        # Categories
        hamburguer = Category(name='Hambúrguer')
        pizza = Category(name='Pizza')
        combo = Category(name='Combos')
        bebida = Category(name='Bebidas')
        db.session.add_all([hamburguer, pizza, combo, bebida])
        db.session.commit()

        # Products
        products = [
            # Hambúrgueres
            Product(name='Gordin Bacon', description='Hambúrguer bovino 150g, muito bacon crocante, cheddar, alface e tomate.', price=28.90, image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=600', category=hamburguer),
            Product(name='Gordin Egg', description='Hambúrguer bovino 150g, ovo frito, queijo mussarela, alface, tomate e maionese da casa.', price=26.50, image_url='https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=600', category=hamburguer),
            Product(name='Gordin Salad', description='Hambúrguer bovino 150g, queijo, cebola roxa, picles, alface e tomate.', price=24.00, image_url='https://images.unsplash.com/photo-1571091718767-18b5b1457add?q=80&w=600', category=hamburguer),
            
            # Pizzas
            Product(name='Pizza Gordin Especial', description='Molho de tomate, mussarela, calabresa, bacon, ovos, cebola, pimentão e orégano.', price=45.00, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=600', category=pizza),
            Product(name='Pizza Margherita', description='Molho de tomate, mussarela, manjericão fresco e tomate fatiado.', price=38.00, image_url='https://images.unsplash.com/photo-1574071318508-1cdbad80ad38?q=80&w=600', category=pizza),
            Product(name='Pizza Portuguesa', description='Mussarela, presunto, ovos, cebola, azeitona e ervilha.', price=42.00, image_url='https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?q=80&w=600', category=pizza),

            # Combos
            Product(name='Combo Casal', description='2 Gordin Bacon + Batata Frita Grande + Coca-Cola 1.5L.', price=85.00, image_url='https://images.unsplash.com/photo-1521305916504-4a1121188589?q=80&w=600', category=combo),
            Product(name='Combo Kids', description='Gordin Salad (mini) + Batata Pequena + Suco de Laranja.', price=32.00, image_url='https://images.unsplash.com/photo-1460306423018-032021f44ddc?q=80&w=600', category=combo),

            # Bebidas
            Product(name='Coca-Cola 2L', description='Refrigerante 2 litros.', price=12.00, image_url='https://images.unsplash.com/photo-1622483767028-3f66f32aef97?q=80&w=600', category=bebida),
            Product(name='Suco Natural', description='Laranja ou Abacaxi com hortelã 500ml.', price=10.00, image_url='https://images.unsplash.com/photo-1544145945-f904253db0ad?q=80&w=600', category=bebida),
        ]
        db.session.add_all(products)

        # Neighborhoods
        neighborhood_names = [
            'Laranjeiras', 'Planalto', 'Cruzeiro Celeste', 'Promorar', 
            'Estrela Dalva', 'Nova Monlevade', 'Loanda', 'Novo Cruzeiro', 'Santo Hipólito'
        ]
        neighborhoods = [Neighborhood(name=name, delivery_fee=7.0) for name in neighborhood_names]
        db.session.add_all(neighborhoods)

        # Admin User
        admin_user = User(
            username='admin', 
            email='admin@gordinlanches.com', 
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed()
