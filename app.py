import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Category, Product, Neighborhood, Order, OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gordin_lanches_chave_super_secreta_2026')

# Na Vercel, usar /tmp (única pasta com permissão de escrita)
# Localmente, usar a pasta instance/
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/gordin.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gordin.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ── Admin ────────────────────────────────────────────────────────────────────

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink

class AdminModelView(ModelView):
    can_export = True
    can_view_details = True
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

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

admin = Admin(app, name='Painel de Gestão', template_mode='bootstrap3')
admin.add_link(MenuLink(name='← Voltar ao Site', category='', url='/'))
admin.add_view(OrderView(Order, db.session, name='Pedidos'))
admin.add_view(CategoryView(Category, db.session, name='Categorias', category='Catalogo'))
admin.add_view(ProductView(Product, db.session, name='Produtos', category='Catalogo'))
admin.add_view(UserView(User, db.session, name='Usuarios', category='Configuracoes'))
admin.add_view(NeighborhoodView(Neighborhood, db.session, name='Taxas de Entrega', category='Configuracoes'))


# ── Rotas ────────────────────────────────────────────────────────────────────

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

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
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

# ── Inicialização do Banco ─────────────────────────────────────────────────

def init_db():
    db.create_all()
    if not Category.query.first():
        # Categorias
        hamburguer = Category(name='Hambúrguer')
        pizza      = Category(name='Pizza')
        combos     = Category(name='Combos')
        bebidas    = Category(name='Bebidas')
        db.session.add_all([hamburguer, pizza, combos, bebidas])
        db.session.flush()  # gera os IDs antes de criar os produtos

        # Bairros
        db.session.add_all([
            Neighborhood(name='Carneirinhos',    delivery_fee=5.0),
            Neighborhood(name='Vila Tanque',     delivery_fee=7.0),
            Neighborhood(name='Loanda',          delivery_fee=6.0),
            Neighborhood(name='Cruzeiro Celeste',delivery_fee=8.0),
            Neighborhood(name='Belmonte',        delivery_fee=6.5),
        ])

        # Usuário admin
        db.session.add(User(
            username='admin',
            email='admin@gordinlanches.com',
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
            is_admin=True
        ))

        # Produtos de exemplo — Hambúrgueres
        db.session.add_all([
            Product(name='X-Burguer Clássico',    description='Hambúrguer artesanal, queijo cheddar, alface e tomate.',         price=22.90, category=hamburguer, is_available=True,
                    image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'),
            Product(name='X-Bacon Duplo',          description='Dois burgers, bacon crocante, queijo e molho especial.',         price=32.90, category=hamburguer, is_available=True,
                    image_url='https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400'),
            Product(name='Smash Burger',           description='Burger prensado na chapa, caramelizado e super saboroso.',       price=28.90, category=hamburguer, is_available=True,
                    image_url='https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400'),
            Product(name='Frango Crispy',          description='Filé de frango empanado, alface americana e maionese.',         price=24.90, category=hamburguer, is_available=True,
                    image_url='https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400'),
        ])

        # Produtos de exemplo — Pizzas
        db.session.add_all([
            Product(name='Pizza Calabresa',        description='Molho de tomate, calabresa fatiada e cebola roxa.',             price=42.90, category=pizza, is_available=True,
                    image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Pizza Mussarela',        description='Molho de tomate, mussarela derretida e manjericão fresco.',     price=39.90, category=pizza, is_available=True,
                    image_url='https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400'),
            Product(name='Pizza Frango c/ Catupiry',description='Frango desfiado, catupiry cremoso e milho verde.',             price=46.90, category=pizza, is_available=True,
                    image_url='https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400'),
            Product(name='Pizza Portuguesa',       description='Presunto, ovos, mussarela, azeitona e cebola.',                price=44.90, category=pizza, is_available=True,
                    image_url='https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?w=400'),
        ])

        # Produtos de exemplo — Bebidas
        db.session.add_all([
            Product(name='Coca-Cola Lata 350ml',    description='Gelada e refrescante.',                                                    price=6.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400'),
            Product(name='Coca-Cola 1 Litro',       description='Garrafa de 1 litro gelada, perfeita para dividir.',                        price=9.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400'),
            Product(name='Coca-Cola 2 Litros',      description='Garrafa família de 2 litros, ideal para acompanhar o pedido da turma.',     price=14.00, category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400'),
            Product(name='Pepsi Lata 350ml',        description='Sabor único e refrescante, bem geladinha.',                                price=6.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400'),
            Product(name='Pepsi 1 Litro',           description='Garrafa de 1 litro da Pepsi geladinha.',                                   price=9.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400'),
            Product(name='Kuat Lata 350ml',         description='Guaraná Kuat geladinho, sabor suave e refrescante.',                       price=6.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1581098365948-6a5a912b7a49?w=400'),
            Product(name='Kuat 1 Litro',            description='Garrafa de 1 litro do Kuat, levinho e refrescante.',                       price=9.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1581098365948-6a5a912b7a49?w=400'),
            Product(name='Refrigerante Mini (Lata 220ml)', description='Latinha gelada, opção individual — diversas marcas disponíveis.',   price=4.50,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1567591370078-f5db83b20872?w=400'),
            Product(name='Suco de Laranja Natural', description='Laranja espremida na hora, sem conservantes.',                             price=10.00, category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400'),
            Product(name='Água Mineral 500ml',      description='Água gelada sem gás.',                                                     price=4.00,  category=bebidas, is_available=True,
                    image_url='https://images.unsplash.com/photo-1564419320461-6870880221ad?w=400'),
        ])

        # Produtos de exemplo — Combos
        db.session.add_all([
            Product(name='Combo X-Burguer + Fritas + Refri', description='X-Burguer clássico + porção de fritas + refrigerante lata.', price=34.90, category=combos, is_available=True,
                    image_url='https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=400'),
            Product(name='Combo Família Pizza Grande',       description='1 Pizza grande + 2 refrigerantes lata.',                     price=69.90, category=combos, is_available=True,
                    image_url='https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=400'),
        ])

        db.session.commit()

with app.app_context():
    try:
        init_db()
    except Exception as e:
        db.session.rollback()
        print(f"[AVISO] init_db falhou: {e}")

if __name__ == '__main__':
    app.run(debug=True)
