import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
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
from flask_admin.theme import Bootstrap4Theme

class AdminModelView(ModelView):
    can_export = True
    can_view_details = True
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class UserView(AdminModelView):
    column_labels = {'username': 'Nome de Usuário', 'email': 'E-mail', 'is_admin': 'Administrador', 'password_hash': 'Senha Nova'}
    column_list = ['id', 'username', 'email', 'is_admin']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin']
    column_editable_list = ['is_admin']
    form_columns = ['username', 'email', 'password_hash', 'is_admin']

    def on_model_change(self, form, model, is_created):
        # Hash da senha se foi preenchida na criacao/edicao
        if form.password_hash.data and not form.password_hash.data.startswith('pbkdf2:sha256'):
            model.password_hash = generate_password_hash(form.password_hash.data, method='pbkdf2:sha256')
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
    inline_models = [OrderItem]
    column_list = ['id', 'user', 'customer_name', 'customer_phone', 'neighborhood', 'address', 'total_price', 'status', 'date_ordered']
    column_searchable_list = ['address', 'status', 'customer_name']
    column_labels = {
        'user': 'Usuário (se logado)',
        'customer_name': 'Cliente',
        'customer_phone': 'WhatsApp',
        'total_price': 'Valor Total (R$)',
        'status': 'Status do Pedido',
        'address': 'Endereço de Entrega',
        'date_ordered': 'Data e Hora',
        'neighborhood': 'Bairro'
    }
    column_filters = ['status', 'date_ordered', 'total_price']
    column_editable_list = ['status']
    column_default_sort = ('date_ordered', True)

admin = Admin(app, name='Painel de Gestão', theme=Bootstrap4Theme())
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
    all_products = Product.query.filter_by(is_available=True).all()
    return render_template('index.html', categories=categories, products=all_products)

@app.route('/menu')
def menu():
    categories = Category.query.all()
    products = Product.query.filter_by(is_available=True).all()
    return render_template('menu.html', categories=categories, products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        next_url = request.form.get('next_url')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(next_url or url_for('index'))
        flash('Email ou senha inválidos.')
        return redirect(url_for('login', next=next_url))
        
    next_url = request.args.get('next') or request.referrer or url_for('index')
    if '/login' in next_url or '/register' in next_url:
        next_url = url_for('index')
    return render_template('login.html', next_url=next_url)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    neighborhoods = Neighborhood.query.all()
    return render_template('cart.html', neighborhoods=neighborhoods)

@app.route('/orders')
def orders():
    # If logged in as admin or user
    if current_user.is_authenticated:
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_ordered.desc()).all()
        return render_template('orders.html', orders=user_orders, identified=True)
    
    # Check if guest is identified in session
    guest_name = session.get('guest_name')
    guest_phone = session.get('guest_phone')
    
    if guest_name and guest_phone:
        # Fetch orders by name and phone
        user_orders = Order.query.filter_by(customer_name=guest_name, customer_phone=guest_phone).order_by(Order.date_ordered.desc()).all()
        return render_template('orders.html', orders=user_orders, identified=True, guest_name=guest_name)
    
    # Not identified, show form
    return render_template('orders.html', identified=False)

@app.route('/identify_orders', methods=['POST'])
def identify_orders():
    nome = request.form.get('nome', '').strip().title()
    sobrenome = request.form.get('sobrenome', '').strip().title()
    telefone = request.form.get('telefone', '').strip()
    
    if not nome or not sobrenome or not telefone:
        flash('Por favor, preencha todos os campos.')
        return redirect(url_for('orders'))
    
    full_name = f"{nome} {sobrenome}"
    session['guest_name'] = full_name
    session['guest_phone'] = telefone
    return redirect(url_for('orders'))

@app.route('/forget_guest')
def forget_guest():
    session.pop('guest_name', None)
    session.pop('guest_phone', None)
    return redirect(url_for('index'))

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

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        address = data.get('address')
        neighborhood_id = data.get('neighborhood_id')
        delivery_fee = data.get('delivery_fee', 0)
        total_price = data.get('total_price', 0)
        items = data.get('items', [])
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        
        if not address or not neighborhood_id or not items:
            return jsonify({'success': False, 'message': 'Endereço, bairro ou itens faltando.'}), 400
            
        # Para visitantes, nome e fone são obrigatórios se não logado
        if not current_user.is_authenticated and (not customer_name or not customer_phone):
            return jsonify({'success': False, 'message': 'Nome e WhatsApp são obrigatórios para finalizar o pedido.'}), 400

        # Extrair observações do nome do item para salvar no endereço para o painel admin
        observations = [f"{item['quantity']}x {item['name']}" for item in items if '(Obs:' in item['name']]
        final_address = address
        if observations:
            final_address += f" | NOTAS: {', '.join(observations)}"

        new_order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=customer_name or (current_user.username if current_user.is_authenticated else "Visitante"),
            customer_phone=customer_phone or "",
            address=final_address,
            neighborhood_id=neighborhood_id,
            delivery_fee=delivery_fee,
            total_price=total_price,
            status='Pending'
        )
        db.session.add(new_order)
        db.session.flush() 
        
        for item in items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.get('product_id'),
                quantity=item.get('quantity', 1),
                price_at_order=item.get('price', 0)
            )
            db.session.add(order_item)
            
        db.session.commit()
        
        # Save guest session automatically after first order
        if not current_user.is_authenticated and customer_name and customer_phone:
            session['guest_name'] = customer_name
            session['guest_phone'] = customer_phone

        return jsonify({'success': True, 'order_id': new_order.id})
    except Exception as e:
        db.session.rollback()
        print(f"Checkout Error: {str(e)}")
        # Em produção, não queremos expor detalhes sensíveis, mas uma mensagem útil ajuda
        return jsonify({'success': False, 'message': 'Erro interno ao processar o pedido no banco de dados.'}), 500

# ── Inicialização do Banco ─────────────────────────────────────────────────

def init_db():
    db.create_all()
    if not Category.query.first():
        # Categorias
        hamburguer = Category(name='Hambúrguer')
        pizza_g    = Category(name='Pizzas (Grande)')
        pizza_m    = Category(name='Pizzas (Média)')
        pizza_p    = Category(name='Pizzas (Pequena)')
        pizza_doce = Category(name='Pizzas Doces (Brotinho)')
        bordas     = Category(name='Bordas Recheadas')
        combos     = Category(name='Combos')
        bebidas    = Category(name='Bebidas')
        db.session.add_all([hamburguer, pizza_g, pizza_m, pizza_p, pizza_doce, bordas, combos, bebidas])
        db.session.flush()  # gera os IDs antes de criar os produtos

        # Bairros (João Monlevade)
        db.session.add_all([
            Neighborhood(name='Areia Preta',      delivery_fee=7.0),
            Neighborhood(name='Baú',              delivery_fee=7.0),
            Neighborhood(name='Belmonte',         delivery_fee=7.0),
            Neighborhood(name='Carneirinhos',     delivery_fee=5.0),
            Neighborhood(name='Centro',           delivery_fee=7.0),
            Neighborhood(name='Cruzeiro Celeste', delivery_fee=8.0),
            Neighborhood(name='Distrito Industrial', delivery_fee=10.0),
            Neighborhood(name='Estrela Dalva',    delivery_fee=7.0),
            Neighborhood(name='José Elói',        delivery_fee=7.0),
            Neighborhood(name='Laranjeiras',      delivery_fee=7.0),
            Neighborhood(name='Loanda',           delivery_fee=6.0),
            Neighborhood(name='Lourdes',          delivery_fee=7.0),
            Neighborhood(name='Novo Cruzeiro',    delivery_fee=7.0),
            Neighborhood(name='Palmares',         delivery_fee=7.0),
            Neighborhood(name='Planalto',         delivery_fee=7.0),
            Neighborhood(name='República',        delivery_fee=7.0),
            Neighborhood(name='Santa Bárbara',    delivery_fee=7.0),
            Neighborhood(name='Santa Cecília',    delivery_fee=7.0),
            Neighborhood(name='Santo Hipólito',   delivery_fee=7.0),
            Neighborhood(name='Satélite',         delivery_fee=7.0),
            Neighborhood(name='Sion',             delivery_fee=7.0),
            Neighborhood(name='Teresópolis',      delivery_fee=7.0),
            Neighborhood(name='Vila Tanque',      delivery_fee=7.0),
            Neighborhood(name='Vila São Geraldo', delivery_fee=7.0),
            Neighborhood(name='Vila Santa Cecília', delivery_fee=7.0),
            Neighborhood(name='Vila Trabalhista',  delivery_fee=7.0),
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
            Product(name='Hambúrguer',            description='Pão, 2 bifes, cheddar, catupiry, milho, batata palha, alface e tomate.',         price=17.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'),
            Product(name='X-Burguer',             description='Pão, 2 bifes, mussarela, cheddar, catupiry, milho, batata palha, alface e tomate.', price=19.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400'),
            Product(name='X-Egg',                 description='Pão, 2 bifes, mussarela, ovo, cheddar, catupiry, milho, batata palha, alface e tomate.', price=21.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400'),
            Product(name='Bacon Burguer',         description='Pão, 2 bifes, bacon, cheddar, catupiry, milho, batata palha, alface e tomate.',  price=22.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400'),
            Product(name='X-Bacon',               description='Pão, 2 bifes, mussarela, bacon, cheddar, catupiry, milho, batata palha, alface e tomate.', price=24.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=400'),
            Product(name='X-Egg Bacon',           description='Pão, 2 bifes, mussarela, ovo, bacon, cheddar, catupiry, milho, batata palha, alface e tomate.', price=26.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=400'),
            Product(name='X-Tudo',                description='Pão, 2 bifes, mussarela, presunto, ovo, bacon, cheddar, catupiry, milho, batata palha, alface e tomate.', price=27.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'),
            Product(name='X-Gordin',              description='Pão, 3 bifes, 2 mussarelas, 2 presuntos, 2 ovos, bacon, cheddar, catupiry, milho, batata palha, alface e tomate.', price=31.00, category=hamburguer, is_available=True, image_url='https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400'),
        ])

        # Produtos de exemplo — Pizzas Tradicionais e Doces
        traditional_flavors = [
            ('Frango c/catupiry', 'Molho de tomate, mussarela, frango, catupiry, milho, palmito, azeitona, mussarela e orégano.', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400'),
            ('Frango c/cheddar', 'Molho de tomate, mussarela, frango, palmito, azeitona, cheddar, e orégano.', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400'),
            ('Portuguesa', 'Molho de tomate, mussarela, presunto, bacon, palmito, ovo cozido, tomate, azeitona, cebola e orégano.', 'https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?w=400'),
            ('Calabresa', 'Molho de tomate, mussarela, calabresa, cebola, pimentão e orégano.', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            ('Bacon c/cheddar', 'Molho de tomate, mussarela, bacon, cheddar, cebola e orégano.', 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            ('A moda da casa', 'Molho de tomate, mussarela, bacon, frango, calabresa, palmito, cebola, pimentão, azeitona, milho, catupiry e orégano.', 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400'),
            ('Vegetariana', 'Molho de tomate, mussarela, palmito, milho, tomate, cebola, pimentão, azeitona e orégano.', 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400'),
            ('Milho c/catupiry', 'Molho de tomate, mussarela, milho, catupiry e orégano.', 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400'),
        ]
        for name, desc, img in traditional_flavors:
            db.session.add(Product(name=f"{name} (Grande)", description=desc, price=64.90, category=pizza_g, is_available=True, image_url=img))
            db.session.add(Product(name=f"{name} (Média)", description=desc, price=54.90, category=pizza_m, is_available=True, image_url=img))
            db.session.add(Product(name=f"{name} (Pequena)", description=desc, price=44.90, category=pizza_p, is_available=True, image_url=img))

        # Pizzas Doces
        db.session.add_all([
            Product(name='Chocolate', description='Chocolate ao leite derretido, granulado.', price=35.90, category=pizza_doce, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Banana Nevada', description='Banana em rodelas, açúcar, canela, mussarela, leite condensado, chocolate branco.', price=35.90, category=pizza_doce, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Romeu e Julieta', description='Queijo mussarela, goiabada derretida.', price=35.90, category=pizza_doce, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Beijinho', description='Creme de ninho, coco ralado, bombom de beijinho.', price=44.90, category=pizza_doce, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Nutella c/ morango', description='Nutella, morango.', price=44.90, category=pizza_doce, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
        ])
        
        # Bordas
        db.session.add_all([
            Product(name='Borda de Catupiry', description='Adicional de Borda recheada - Catupiry.', price=15.00, category=bordas, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Borda de Cheddar', description='Adicional de Borda recheada - Cheddar.', price=20.00, category=bordas, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
            Product(name='Borda de Chocolate', description='Adicional de Borda recheada - Chocolate.', price=20.00, category=bordas, is_available=True, image_url='https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'),
        ])

        # Produtos de exemplo — Bebidas
        db.session.add_all([
            Product(name='Refri Mini',              description='Lata ou mini pet bem gelada.', price=3.00,  category=bebidas, is_available=True, image_url='/static/img/refri_mini.jpg'),
            Product(name='Refrigerante 1L',         description='Garrafa de 1 litro.', price=8.00,  category=bebidas, is_available=True, image_url='/static/img/cola_1l.jpg'),
            Product(name='Kuat 2L',                 description='Garrafa de 2 litros do Guaraná Kuat.', price=10.00, category=bebidas, is_available=True, image_url='/static/img/kuat_2l.jpg'),
            Product(name='Fanta 2L',                description='Fanta Laranja 2 Litros.', price=14.00, category=bebidas, is_available=True, image_url='/static/img/fanta_2l.jpg'),
            Product(name='Coca 2 L',                description='Garrafa família de 2 litros gelada.', price=16.00, category=bebidas, is_available=True, image_url='/static/img/coca_2l.jpg'),
        ])

        # Produtos de exemplo — Combos
        db.session.add_all([
            Product(name='Combo X-Bacon', description='X-Bacon + 100g de batata + um refrigerante mini.', price=28.90, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=400'),
            Product(name='Combo X-Tudo', description='X-Tudo + 100g de batata + um refrigerante mini.', price=31.90, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'),
            Product(name='Combo X-Egg', description='X-Egg + 100g de batata + um refrigerante mini.', price=27.90, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1596662951482-0c4ba74a6df6?w=400'),
            Product(name='Combo Casal', description='1x X-Bacon + 1x X-Tudo + porção de batata + refrigerante 1L.', price=60.90, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1550547660-d9450f859349?w=400'),
            Product(name='Combo Ideal', description='03 hambúrgueres + porção de batata + bebida.', price=69.90, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1521305916504-4a1121188589?w=400'),
            Product(name='Combo Duplo X-Gordin', description='2x X-Gordin + porção de fritas + refrigerante 1L.', price=75.00, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400'),
            Product(name='Combo Duplo X-Bacon', description='2x X-Bacon + porção de fritas + refrigerante 1L.', price=55.00, category=combos, is_available=True, image_url='https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=400'),
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
