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

# Vercel's filesystem is completely locked down.
# We MUST use an in-memory database to prevent 500 crashes on boot.
import os
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gordin_lanches.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Base Admin View
# Base Admin View
class AdminModelView(ModelView):
    can_export = True
    can_view_details = True
    page_size = 50
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Specific views with Portuguese labels
class UserView(AdminModelView):
    column_labels = {'username': 'Nome de Usuário', 'email': 'E-mail', 'is_admin': 'Administrador'}
    column_list = ['id', 'username', 'email', 'is_admin']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin']
    column_editable_list = ['is_admin']

class CategoryView(AdminModelView):
    column_labels = {'name': 'Nome da Categoria'}
    column_list = ['id', 'name']
    column_searchable_list = ['name']

class ProductView(AdminModelView):
    column_labels = {
        'name': 'Nome do Produto',
        'price': 'Preço (R$)',
        'description': 'Descrição',
        'image_url': 'Link da Imagem',
        'is_available': 'Disponível no Site',
        'category': 'Categoria'
    }
    column_list = ['id', 'name', 'category', 'price', 'is_available']
    column_searchable_list = ['name', 'description']
    column_filters = ['category.name', 'is_available', 'price']
    column_editable_list = ['price', 'is_available']

class NeighborhoodView(AdminModelView):
    column_labels = {'name': 'Bairro', 'delivery_fee': 'Taxa de Entrega (R$)'}
    column_list = ['id', 'name', 'delivery_fee']
    column_searchable_list = ['name']
    column_editable_list = ['delivery_fee']

class OrderView(AdminModelView):
    column_labels = {
        'user': 'Cliente',
        'total_price': 'Valor Total (R$)',
        'status': 'Status do Pedido',
        'address': 'Endereço de Entrega',
        'date_ordered': 'Data e Hora',
        'neighborhood': 'Bairro'
    }
    column_list = ['id', 'user', 'total_price', 'status', 'date_ordered']
    column_searchable_list = ['address', 'status']
    column_filters = ['status', 'date_ordered', 'total_price']
    column_editable_list = ['status']
    column_default_sort = ('date_ordered', True)

from flask_admin.menu import MenuLink

# Admin Initialization
admin = Admin(app, name='Painel de Gestão', theme=Bootstrap4Theme())
admin.add_link(MenuLink(name='Voltar ao Site', category='', url='/'))

# Adding localized views
admin.add_view(OrderView(Order, db.session, name='📦 Pedidos'))
admin.add_view(CategoryView(Category, db.session, name='Categorias', category='🍔 Catálogo'))
admin.add_view(ProductView(Product, db.session, name='Produtos', category='🍔 Catálogo'))
admin.add_view(UserView(User, db.session, name='Usuários', category='⚙️ Configurações'))
admin.add_view(NeighborhoodView(Neighborhood, db.session, name='Taxas de Entrega', category='⚙️ Configurações'))

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
        flash('Email ou senha inválidos.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email já cadastrado.')
            return redirect(url_for('register'))
            
        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash('Nome de usuário já está em uso. Por favor, escolha outro.')
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
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
