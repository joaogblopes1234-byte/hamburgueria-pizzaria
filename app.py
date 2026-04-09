import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from models import db, User, Category, Product, Neighborhood, Order, OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Vercel's filesystem is mostly read-only.
# We try to use /tmp/ first, but if anything fails we fallback to memory.
import os
db_path = '/tmp/gordin_lanches.db' if os.environ.get('VERCEL') else 'gordin_lanches.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Base Admin View
class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Specific views with Portuguese labels
class UserView(AdminModelView):
    column_labels = {'username': 'Nome de Usuário', 'email': 'E-mail', 'is_admin': 'Administrador'}
    column_list = ['username', 'email', 'is_admin']

class CategoryView(AdminModelView):
    column_labels = {'name': 'Nome da Categoria'}

class ProductView(AdminModelView):
    column_labels = {
        'name': 'Nome do Produto',
        'price': 'Preço (R$)',
        'description': 'Descrição',
        'image_url': 'Link da Imagem',
        'is_available': 'Disponível no Site',
        'category': 'Categoria'
    }

class NeighborhoodView(AdminModelView):
    column_labels = {'name': 'Bairro', 'delivery_fee': 'Taxa de Entrega (R$)'}

class OrderView(AdminModelView):
    column_labels = {
        'user': 'Cliente',
        'total_price': 'Valor Total',
        'status': 'Status do Pedido',
        'address': 'Endereço de Entrega',
        'created_at': 'Data e Hora'
    }
    column_list = ['id', 'user', 'total_price', 'status', 'created_at']

from flask_admin.menu import MenuLink

# Admin Initialization
admin = Admin(app, name='Painel Gordin Lanches', theme=Bootstrap4Theme())
admin.add_link(MenuLink(name='Voltar ao Site', category='', url='/'))

# Adding localized views
admin.add_view(UserView(User, db.session, name='Usuários'))
admin.add_view(CategoryView(Category, db.session, name='Categorias'))
admin.add_view(ProductView(Product, db.session, name='Produtos'))
admin.add_view(NeighborhoodView(Neighborhood, db.session, name='Bairros e Entrega'))
admin.add_view(OrderView(Order, db.session, name='Pedidos'))

# Routes
@app.route('/')
def index():
    categories = Category.query.all()
    featured_products = Product.query.filter_by(is_available=True).limit(8).all()
    return render_template('index.html', categories=categories, products=featured_products)

@app.route('/menu')
def menu():
    categories = Category.query.all()
    products = Product.query.filter_by(is_available=True).all()
    return render_template('menu.html', categories=categories, products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Email ou senha invlidos.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email j cadastrado.')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username, 
            email=email, 
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    neighborhoods = Neighborhood.query.all()
    return render_template('cart.html', neighborhoods=neighborhoods)

@app.route('/api/products')
def api_products():
    products = Product.query.filter_by(is_available=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'description': p.description,
        'image_url': p.image_url,
        'category': p.category.name
    } for p in products])

def init_db():
    try:
        db.create_all()
        if not Category.query.first():
            hamburguer = Category(name='Hambúrguer')
            pizza = Category(name='Pizza')
            combo = Category(name='Combos')
            bebida = Category(name='Bebidas')
            db.session.add_all([hamburguer, pizza, combo, bebida])
            
            n1 = Neighborhood(name='Carneirinhos', delivery_fee=5.0)
            n2 = Neighborhood(name='Vila Tanque', delivery_fee=7.0)
            n3 = Neighborhood(name='Loanda', delivery_fee=6.0)
            n4 = Neighborhood(name='Cruzeiro Celeste', delivery_fee=8.0)
            n5 = Neighborhood(name='Belmonte', delivery_fee=6.5)
            db.session.add_all([n1, n2, n3, n4, n5])
            
            admin_user = User(
                username='admin', 
                email='admin@gordinlanches.com', 
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

with app.app_context():
    try:
        init_db()
    except Exception as e:
        # Fallback to in-memory database on Vercel deployment crash
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        init_db()

if __name__ == '__main__':
    app.run(debug=True)
