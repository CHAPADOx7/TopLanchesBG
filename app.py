import os
import json
from datetime import datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy import or_, func, inspect, text
from urllib import request as urllib_request, error as urllib_error

import config
from models import db, Usuario, Cliente, Entregador, Produto, Combo, Cupom, Banner, FormaPagamento, TaxaEntrega, Pedido, ItemPedido, Configuracao, ParametroSistema, HistoricoAlteracao

app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'img', 'uploads')
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)
# Use o modo assíncrono padrão do Flask-SocketIO para compatibilidade.
# Se quiser eventlet, instale e configure manualmente.
socketio = SocketIO(app, cors_allowed_origins='*')

ROLE_ADMIN = config.ROLE_ADMIN
ROLE_CLIENT = config.ROLE_CLIENT
ROLE_DELIVERY = config.ROLE_DELIVERY


def init_app():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        ensure_pedido_order_number_column()
        if not Configuracao.query.first():
            db.session.add(Configuracao(horario_abertura='17:00', horario_fechamento='00:00', whatsapp_empresa='552299568835', taxa_fixa=5.00, entrega_ativa=True))
            db.session.commit()
        if not Usuario.query.filter_by(usuario='admin').first():
            senha = generate_password_hash('admin123', method='pbkdf2:sha256', salt_length=12)
            db.session.add(Usuario(nome='Administrador', usuario='admin', senha_hash=senha, nivel=ROLE_ADMIN, ativo=True))
            db.session.commit()
        if not Entregador.query.filter_by(usuario='entregador').first():
            senha_ent = generate_password_hash('entregador123', method='pbkdf2:sha256', salt_length=12)
            db.session.add(Entregador(nome='Entregador Teste', telefone='(22) 99999-9999', usuario='entregador', senha_hash=senha_ent, ativo=True))
            db.session.commit()
        defaults = [
            ('Dinheiro em especie', 'Pagamento em dinheiro', True),
            ('Cartao de credito', 'Credito', False),
            ('Cartao de debito', 'Debito', False),
            ('PIX', 'Pagamento instantaneo', False),
            ('Outras', 'Voucher e outros', False),
        ]
        for nome, descricao, aceita_troco in defaults:
            if not FormaPagamento.query.filter(func.lower(FormaPagamento.nome) == nome.lower()).first():
                db.session.add(FormaPagamento(nome=nome, descricao=descricao, ativo=True, aceita_troco=aceita_troco, valor_troco=0))
        if not ParametroSistema.query.filter_by(chave='tempo_espera_minutos').first():
            db.session.add(ParametroSistema(chave='tempo_espera_minutos', valor='35'))
        if not ParametroSistema.query.filter_by(chave='pedido_ordem_atual').first():
            db.session.add(ParametroSistema(chave='pedido_ordem_atual', valor='0'))
        if not ParametroSistema.query.filter_by(chave='kitchen_printer_enabled').first():
            db.session.add(ParametroSistema(chave='kitchen_printer_enabled', valor='false'))
        if not ParametroSistema.query.filter_by(chave='kitchen_printer_name').first():
            db.session.add(ParametroSistema(chave='kitchen_printer_name', valor=''))
        if not ParametroSistema.query.filter_by(chave='general_printer_enabled').first():
            db.session.add(ParametroSistema(chave='general_printer_enabled', valor='false'))
        if not ParametroSistema.query.filter_by(chave='general_printer_name').first():
            db.session.add(ParametroSistema(chave='general_printer_name', valor=''))
        if not ParametroSistema.query.filter_by(chave='site_theme').first():
            db.session.add(ParametroSistema(chave='site_theme', valor='normal'))
        db.session.commit()


@app.context_processor
def inject_user():
    config_obj = Configuracao.query.first()
    return {
        'current_role': session.get('user_role'),
        'current_name': session.get('user_name'),
        'current_endpoint': request.endpoint,
        'delivery_open': bool(config_obj.entrega_ativa) if config_obj else True,
        'site_theme': get_param('site_theme', 'normal'),
    }


def role_required(role):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if session.get('user_role') != role:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTENSIONS']


def save_uploaded_image(file_storage):
    if file_storage and file_storage.filename and allowed_image_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file_storage.save(upload_path)
        return f"uploads/{unique_name}"
    return None


def get_delivery_fee(bairro):
    taxa = TaxaEntrega.query.filter_by(bairro=bairro, ativo=True).first()
    if taxa:
        return float(taxa.valor)
    config_obj = Configuracao.query.first()
    return float(config_obj.taxa_fixa if config_obj else config.DEFAULT_DELIVERY_FEE)


def get_param(chave, default_value=''):
    param = ParametroSistema.query.filter_by(chave=chave).first()
    if not param:
        return default_value
    return param.valor


def set_param(chave, valor):
    param = ParametroSistema.query.filter_by(chave=chave).first()
    if not param:
        param = ParametroSistema(chave=chave, valor=str(valor))
        db.session.add(param)
    else:
        param.valor = str(valor)
    return param


def get_next_order_number():
    current = int(get_param('pedido_ordem_atual', '0') or 0)
    next_number = current + 1
    set_param('pedido_ordem_atual', str(next_number))
    return next_number


def reset_order_number_counter():
    set_param('pedido_ordem_atual', '0')


def get_order_display_number(pedido):
    return pedido.numero_pedido or pedido.id


def ensure_pedido_order_number_column():
    inspector = inspect(db.engine)
    columns = {column['name'] for column in inspector.get_columns('pedidos')}
    if 'numero_pedido' not in columns:
        db.session.execute(text('ALTER TABLE pedidos ADD COLUMN numero_pedido INTEGER'))
        db.session.commit()


def whatsapp_business_enabled():
    return get_param('whatsapp_business_enabled', 'false').lower() == 'true'


def whatsapp_business_config():
    return {
        'enabled': whatsapp_business_enabled(),
        'token': get_param('whatsapp_business_token', '').strip(),
        'phone_id': get_param('whatsapp_business_phone_id', '').strip(),
        'api_version': get_param('whatsapp_business_api_version', 'v20.0').strip() or 'v20.0',
    }


def normalize_whatsapp_number(phone):
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if not digits:
        return ''
    if digits.startswith('55'):
        return digits
    return f'55{digits}'


def build_order_summary(pedido):
    order_number = get_order_display_number(pedido)
    linhas = [
        f'Pedido #{order_number}',
        f'Cliente: {pedido.nome}',
        f'Telefone: {pedido.telefone}',
        f'Endereco: {pedido.endereco}, {pedido.bairro}',
        f'Pagamento: {pedido.forma_pagamento}',
        f'Total: R$ {float(pedido.valor_total):.2f}'.replace('.', ','),
    ]
    if pedido.observacao:
        linhas.append(f'Observacao: {pedido.observacao}')
    linhas.append('Itens:')
    for item in pedido.itens:
        linhas.append(f'- {item.quantidade}x {item.nome}')
    return '\n'.join(linhas)


def send_whatsapp_message(phone, message):
    config_obj = whatsapp_business_config()
    if not config_obj['enabled'] or not config_obj['token'] or not config_obj['phone_id']:
        return False
    to_number = normalize_whatsapp_number(phone)
    if not to_number:
        return False
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'text',
        'text': {'body': message},
    }
    url = f"https://graph.facebook.com/{config_obj['api_version']}/{config_obj['phone_id']}/messages"
    request_obj = urllib_request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config_obj['token']}",
        },
        method='POST'
    )
    try:
        with urllib_request.urlopen(request_obj, timeout=10) as response:
            response.read()
        return True
    except (urllib_error.URLError, urllib_error.HTTPError, TimeoutError, ValueError) as exc:
        app.logger.warning('Falha ao enviar WhatsApp para %s: %s', to_number, exc)
        return False


def notify_order_status(pedido, status, include_summary=False):
    if status == 'Em Preparo':
        prefix = 'Seu pedido foi aceito e esta em preparo.'
    elif status == 'Saiu para Entrega':
        prefix = 'Seu pedido foi despachado para entrega.'
    elif status == 'Entregue':
        prefix = 'Seu pedido foi entregue com sucesso.'
    elif status == 'Arquivado':
        prefix = 'O delivery foi fechado e seu pedido foi arquivado no historico.'
    else:
        prefix = f'Seu pedido mudou para o status: {status}.'
    message = prefix
    if include_summary:
        message = f"{prefix}\n\n{build_order_summary(pedido)}"
    send_whatsapp_message(pedido.telefone, message)


def normalize_next_status(status):
    return 'Em Preparo' if status == 'Aceito' else status


def can_transition_status(current_status, requested_status):
    next_status = normalize_next_status(requested_status)
    flow = {
        'Pendente': {'Em Preparo', 'Recusado'},
        'Aceito': {'Em Preparo', 'Saiu para Entrega'},
        'Em Preparo': {'Saiu para Entrega'},
        'Saiu para Entrega': {'Entregue'},
        'Entregue': set(),
        'Recusado': set(),
        'Arquivado': set(),
    }
    return next_status in flow.get(current_status, set())


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/index.html')
def index_html():
    return redirect(url_for('index'))


@app.route('/css/<path:filename>')
def css_files(filename):
    return send_from_directory('css', filename)


@app.route('/js/<path:filename>')
def js_files(filename):
    return send_from_directory('js', filename)


@app.route('/img/<path:filename>')
def img_files(filename):
    return send_from_directory('img', filename)


@app.route('/view/<path:filename>')
def view_files(filename):
    return send_from_directory('view', filename)


@app.route('/cart.html')
def cart_html():
    return redirect(url_for('cart'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '')

        user = Usuario.query.filter_by(usuario=usuario, ativo=True).first()
        role = ROLE_ADMIN
        if not user:
            user = Entregador.query.filter_by(usuario=usuario, ativo=True).first()
            role = ROLE_DELIVERY if user else ROLE_CLIENT

        if not user:
            user = Cliente.query.filter((Cliente.email == usuario) | (Cliente.telefone == usuario)).first()
            role = ROLE_CLIENT if user else None

        if user and check_password_hash(user.senha_hash, senha):
            session['user_id'] = user.id
            session['user_role'] = role
            session['user_name'] = getattr(user, 'nome', usuario)
            if role == ROLE_ADMIN:
                return redirect(url_for('admin_dashboard'))
            if role == ROLE_DELIVERY:
                return redirect(url_for('delivery_panel'))
            return redirect(url_for('client_orders'))

        flash('Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        aceitou_termos = request.form.get('aceitou_termos') == 'on'

        if not aceitou_termos:
            flash('Você precisa aceitar os termos para criar a conta.', 'warning')
            return redirect(url_for('register'))

        if Cliente.query.filter_by(email=email).first():
            flash('Este e-mail já está em uso.', 'warning')
            return redirect(url_for('register'))

        cliente = Cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            senha_hash=generate_password_hash(senha, method='pbkdf2:sha256', salt_length=12),
            ativo=True
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cadastro realizado com sucesso. Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/client/orders')
@role_required(ROLE_CLIENT)
def client_orders():
    cliente_id = session.get('user_id')
    cliente = Cliente.query.get(cliente_id)
    pedidos_ativos = Pedido.query.filter(
        Pedido.cliente_id == cliente_id,
        Pedido.status.in_(['Pendente', 'Aceito', 'Em Preparo', 'Saiu para Entrega'])
    ).order_by(Pedido.data.desc()).all()
    historico = Pedido.query.filter(
        Pedido.cliente_id == cliente_id,
        ~Pedido.status.in_(['Pendente', 'Aceito', 'Em Preparo', 'Saiu para Entrega'])
    ).order_by(Pedido.data.desc()).all()
    return render_template('client/orders.html', cliente=cliente, pedidos_ativos=pedidos_ativos, historico=historico)


@app.route('/cart')
def cart():
    return render_template('cart.html')


@app.route('/admin/dashboard')
@role_required(ROLE_ADMIN)
def admin_dashboard():
    pedidos = Pedido.query.all()
    produtos = Produto.query.all()
    clientes = Cliente.query.all()
    pendentes = Pedido.query.filter_by(status='Pendente').count()
    aceitos = Pedido.query.filter_by(status='Aceito').count()
    recusados = Pedido.query.filter_by(status='Recusado').count()
    entregues = Pedido.query.filter_by(status='Entregue').count()
    receita_diaria = sum([float(p.valor_total) for p in pedidos if p.data.date() == datetime.utcnow().date()])
    receita_mensal = sum([float(p.valor_total) for p in pedidos if p.data.month == datetime.utcnow().month and p.data.year == datetime.utcnow().year])
    return render_template(
        'admin/dashboard.html',
        pedidos=pedidos,
        produtos=produtos,
        clientes=clientes,
        pendentes=pendentes,
        aceitos=aceitos,
        recusados=recusados,
        entregues=entregues,
        receita_diaria=receita_diaria,
        receita_mensal=receita_mensal
    )


@app.route('/admin/orders')
@role_required(ROLE_ADMIN)
def admin_orders():
    pedidos = Pedido.query.filter(Pedido.status != 'Arquivado').order_by(Pedido.data.desc()).all()
    entregadores = Entregador.query.filter_by(ativo=True).order_by(Entregador.nome).all()
    kitchen_printer_enabled = get_param('kitchen_printer_enabled', 'false').lower() == 'true'
    kitchen_printer_name = get_param('kitchen_printer_name', '')
    return render_template(
        'admin/orders.html',
        pedidos=pedidos,
        entregadores=entregadores,
        kitchen_printer_enabled=kitchen_printer_enabled,
        kitchen_printer_name=kitchen_printer_name,
    )


@app.route('/admin/orders/archived')
@role_required(ROLE_ADMIN)
def admin_orders_archived():
    pedidos_arquivados = Pedido.query.filter_by(status='Arquivado').order_by(Pedido.data.desc()).all()
    grupos_por_data = []
    ultimo_dia = None
    pedidos_dia = []
    for pedido in pedidos_arquivados:
        dia = pedido.data.strftime('%d/%m/%Y')
        if dia != ultimo_dia:
            if pedidos_dia:
                grupos_por_data.append((ultimo_dia, pedidos_dia))
            ultimo_dia = dia
            pedidos_dia = [pedido]
        else:
            pedidos_dia.append(pedido)
    if pedidos_dia:
        grupos_por_data.append((ultimo_dia, pedidos_dia))
    return render_template('admin/orders_archived.html', grupos_por_data=grupos_por_data)


@app.route('/admin/help')
@role_required(ROLE_ADMIN)
def admin_help():
    return render_template('admin/help.html')


@app.route('/admin/products')
@role_required(ROLE_ADMIN)
def admin_products():
    categoria = request.args.get('categoria', '').strip().lower()
    query = Produto.query
    if categoria:
        categoria_db = func.lower(Produto.categoria)
        if categoria == 'lanches':
            query = query.filter(or_(categoria_db == 'lanches', categoria_db == 'lanche'))
        elif categoria == 'combos':
            query = query.filter(or_(categoria_db == 'combos', categoria_db == 'combo'))
        elif categoria == 'bebidas':
            query = query.filter(or_(categoria_db == 'bebidas', categoria_db == 'bebida'))
        elif categoria == 'porcoes':
            query = query.filter(or_(categoria_db == 'porcoes', categoria_db == 'porção', categoria_db == 'porções', categoria_db == 'porcao'))
        elif categoria == 'promocao':
            query = query.filter(or_(categoria_db == 'promocao', categoria_db == 'promoção', categoria_db == 'promocoes', categoria_db == 'promoções'))
    produtos = query.order_by(Produto.nome).all()
    categorias = [
        ('lanches', 'Lanches'),
        ('combos', 'Combos'),
        ('bebidas', 'Bebidas'),
        ('porcoes', 'Porções'),
        ('promocao', 'Promoção')
    ]
    historico = HistoricoAlteracao.query.filter_by(entidade='produto', campo='preco').order_by(HistoricoAlteracao.alterado_em.desc()).limit(20).all()
    return render_template('admin/products.html', produtos=produtos, categoria_atual=categoria, categorias=categorias, historico=historico)


@app.route('/admin/employees')
@role_required(ROLE_ADMIN)
def admin_employees():
    entregadores = Entregador.query.order_by(Entregador.nome).all()
    return render_template('admin/employees.html', entregadores=entregadores)


@app.route('/admin/employees/new', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_employee_new():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '').strip()
        if not nome or not usuario or not senha:
            flash('Nome, usuário e senha são obrigatórios.', 'warning')
            return redirect(url_for('admin_employee_new'))
        if Entregador.query.filter_by(usuario=usuario).first():
            flash('Já existe um entregador com este usuário.', 'warning')
            return redirect(url_for('admin_employee_new'))
        senha_hash = generate_password_hash(senha, method='pbkdf2:sha256', salt_length=12)
        entregador = Entregador(nome=nome, telefone=telefone, usuario=usuario, senha_hash=senha_hash, ativo=True)
        db.session.add(entregador)
        db.session.commit()
        flash('Funcionário cadastrado com sucesso.', 'success')
        return redirect(url_for('admin_employees'))
    return render_template('admin/employee_form.html', entregador=None)


@app.route('/admin/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_employee_edit(employee_id):
    entregador = Entregador.query.get_or_404(employee_id)
    if request.method == 'POST':
        entregador.nome = request.form.get('nome', entregador.nome).strip()
        entregador.telefone = request.form.get('telefone', entregador.telefone).strip()
        entregador.usuario = request.form.get('usuario', entregador.usuario).strip()
        senha = request.form.get('senha', '').strip()
        if senha:
            entregador.senha_hash = generate_password_hash(senha, method='pbkdf2:sha256', salt_length=12)
        entregador.ativo = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('Funcionário atualizado com sucesso.', 'success')
        return redirect(url_for('admin_employees'))
    return render_template('admin/employee_form.html', entregador=entregador)


@app.route('/admin/employees/<int:employee_id>/toggle', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_employee_toggle(employee_id):
    entregador = Entregador.query.get_or_404(employee_id)
    entregador.ativo = not entregador.ativo
    db.session.commit()
    return redirect(url_for('admin_employees'))


@app.route('/admin/employees/<int:employee_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_employee_delete(employee_id):
    entregador = Entregador.query.get_or_404(employee_id)
    db.session.delete(entregador)
    db.session.commit()
    flash('Funcionário removido.', 'success')
    return redirect(url_for('admin_employees'))


@app.route('/admin/products/new', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_product_new():
    if request.method == 'POST':
        imagem_file = request.files.get('imagem_file')
        imagem_upload = save_uploaded_image(imagem_file)
        imagem_value = imagem_upload or request.form.get('imagem', '').strip() or 'burger.png'
        produto = Produto(
            nome=request.form.get('nome', '').strip(),
            descricao=request.form.get('descricao', '').strip(),
            preco=Decimal(request.form.get('preco', '0')),
            imagem=imagem_value,
            estoque=int(request.form.get('estoque', '0')),
            categoria=request.form.get('categoria', '').strip(),
            ativo=request.form.get('ativo') == 'on'
        )
        db.session.add(produto)
        db.session.commit()
        flash('Produto cadastrado com sucesso.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', produto=None)


@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_product_edit(product_id):
    produto = Produto.query.get_or_404(product_id)
    if request.method == 'POST':
        preco_antigo = Decimal(str(produto.preco))
        imagem_file = request.files.get('imagem_file')
        imagem_upload = save_uploaded_image(imagem_file)
        imagem_value = imagem_upload or request.form.get('imagem', produto.imagem or '').strip() or produto.imagem or 'burger.png'
        produto.nome = request.form.get('nome', produto.nome).strip()
        produto.descricao = request.form.get('descricao', produto.descricao).strip()
        produto.preco = Decimal(request.form.get('preco', produto.preco))
        produto.imagem = imagem_value
        produto.estoque = int(request.form.get('estoque', produto.estoque))
        produto.categoria = request.form.get('categoria', produto.categoria).strip()
        produto.ativo = request.form.get('ativo') == 'on'
        if produto.preco != preco_antigo:
            historico = HistoricoAlteracao(
                entidade='produto',
                item_id=produto.id,
                item_nome=produto.nome,
                campo='preco',
                valor_antigo=f"R${float(preco_antigo):.2f}",
                valor_novo=f"R${float(produto.preco):.2f}",
                alterado_por=session.get('user_name', 'Administrador'),
                alterado_em=datetime.utcnow()
            )
            db.session.add(historico)
        db.session.commit()
        flash('Produto atualizado com sucesso.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', produto=produto)


@app.route('/admin/products/<int:product_id>/toggle', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_product_toggle(product_id):
    produto = Produto.query.get_or_404(product_id)
    produto.ativo = not produto.ativo
    db.session.commit()
    return redirect(url_for('admin_products'))


@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_product_delete(product_id):
    produto = Produto.query.get_or_404(product_id)
    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído.', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/taxas')
@role_required(ROLE_ADMIN)
def admin_taxas():
    taxas = TaxaEntrega.query.order_by(TaxaEntrega.bairro).all()
    config_obj = Configuracao.query.first()
    return render_template('admin/taxas.html', taxas=taxas, config_obj=config_obj)


@app.route('/admin/taxas/new', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_tax_new():
    tipo_taxa = request.form.get('tipo_taxa', 'bairro').strip()
    bairro = request.form.get('bairro', '').strip()
    valor = Decimal(request.form.get('valor', '0'))
    ativo = request.form.get('ativo') == 'on'
    if tipo_taxa == 'global':
        config_obj = Configuracao.query.first()
        if not config_obj:
            config_obj = Configuracao()
            db.session.add(config_obj)
        config_obj.taxa_fixa = valor
        db.session.commit()
        flash('Taxa global atualizada.', 'success')
    elif bairro:
        taxa = TaxaEntrega(bairro=bairro, valor=valor, ativo=ativo)
        db.session.add(taxa)
        db.session.commit()
        flash('Taxa de entrega cadastrada.', 'success')
    return redirect(url_for('admin_taxas'))


@app.route('/admin/taxas/<int:taxa_id>/toggle', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_tax_toggle(taxa_id):
    taxa = TaxaEntrega.query.get_or_404(taxa_id)
    taxa.ativo = not taxa.ativo
    db.session.commit()
    return redirect(url_for('admin_taxas'))


@app.route('/admin/taxas/<int:taxa_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_tax_delete(taxa_id):
    taxa = TaxaEntrega.query.get_or_404(taxa_id)
    db.session.delete(taxa)
    db.session.commit()
    flash('Taxa removida.', 'success')
    return redirect(url_for('admin_taxas'))


@app.route('/admin/combos')
@role_required(ROLE_ADMIN)
def admin_combos():
    combos = Combo.query.order_by(Combo.nome).all()
    return render_template('admin/combos.html', combos=combos)


@app.route('/admin/combos/new', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_combo_new():
    if request.method == 'POST':
        validade = request.form.get('validade')
        imagem_file = request.files.get('imagem_file')
        imagem_upload = save_uploaded_image(imagem_file)
        imagem_value = imagem_upload or request.form.get('imagem', '').strip() or 'combo.png'
        combo = Combo(
            nome=request.form.get('nome', '').strip(),
            descricao=request.form.get('descricao', '').strip(),
            preco=Decimal(request.form.get('preco', '0')),
            imagem=imagem_value,
            ativo=request.form.get('ativo') == 'on',
            validade=datetime.fromisoformat(validade) if validade else None
        )
        db.session.add(combo)
        db.session.commit()
        flash('Combo cadastrado com sucesso.', 'success')
        return redirect(url_for('admin_combos'))
    return render_template('admin/combo_form.html', combo=None)


@app.route('/admin/combos/<int:combo_id>/edit', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_combo_edit(combo_id):
    combo = Combo.query.get_or_404(combo_id)
    if request.method == 'POST':
        validade = request.form.get('validade')
        imagem_file = request.files.get('imagem_file')
        imagem_upload = save_uploaded_image(imagem_file)
        imagem_value = imagem_upload or request.form.get('imagem', combo.imagem or '').strip() or combo.imagem or 'combo.png'
        combo.nome = request.form.get('nome', combo.nome).strip()
        combo.descricao = request.form.get('descricao', combo.descricao).strip()
        combo.preco = Decimal(request.form.get('preco', combo.preco))
        combo.imagem = imagem_value
        combo.ativo = request.form.get('ativo') == 'on'
        combo.validade = datetime.fromisoformat(validade) if validade else None
        db.session.commit()
        flash('Combo atualizado com sucesso.', 'success')
        return redirect(url_for('admin_combos'))
    return render_template('admin/combo_form.html', combo=combo)


@app.route('/admin/combos/<int:combo_id>/toggle', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_combo_toggle(combo_id):
    combo = Combo.query.get_or_404(combo_id)
    combo.ativo = not combo.ativo
    db.session.commit()
    return redirect(url_for('admin_combos'))


@app.route('/admin/combos/<int:combo_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_combo_delete(combo_id):
    combo = Combo.query.get_or_404(combo_id)
    db.session.delete(combo)
    db.session.commit()
    flash('Combo excluído.', 'success')
    return redirect(url_for('admin_combos'))


@app.route('/admin/payments')
@role_required(ROLE_ADMIN)
def admin_payments():
    formas = FormaPagamento.query.order_by(FormaPagamento.nome).all()
    return render_template('admin/payments.html', formas=formas)


@app.route('/admin/payments/new', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_payment_new():
    qr_file = request.files.get('qr_code_file')
    qr_upload = save_uploaded_image(qr_file)
    forma = FormaPagamento(
        nome=request.form.get('nome', '').strip(),
        descricao=request.form.get('descricao', '').strip(),
        ativo=request.form.get('ativo') == 'on',
        aceita_troco=request.form.get('aceita_troco') == 'on',
        valor_troco=Decimal(request.form.get('valor_troco', '0')),
        chave_pix=request.form.get('chave_pix', '').strip(),
        qr_code=qr_upload or request.form.get('qr_code', '').strip()
    )
    db.session.add(forma)
    db.session.commit()
    flash('Forma de pagamento adicionada.', 'success')
    return redirect(url_for('admin_payments'))


@app.route('/admin/payments/<int:payment_id>/toggle', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_payment_toggle(payment_id):
    forma = FormaPagamento.query.get_or_404(payment_id)
    forma.ativo = not forma.ativo
    db.session.commit()
    return redirect(url_for('admin_payments'))


@app.route('/admin/payments/<int:payment_id>/delete', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_payment_delete(payment_id):
    forma = FormaPagamento.query.get_or_404(payment_id)
    if forma.nome in ['Dinheiro em especie', 'Cartao de credito', 'Cartao de debito', 'PIX', 'Outras']:
        flash('Formas padrao nao podem ser excluidas, apenas ativadas/desativadas.', 'warning')
        return redirect(url_for('admin_payments'))
    db.session.delete(forma)
    db.session.commit()
    flash('Forma de pagamento excluída.', 'success')
    return redirect(url_for('admin_payments'))


@app.route('/admin/config', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_config():
    config_obj = Configuracao.query.first()
    if not config_obj:
        config_obj = Configuracao()
        db.session.add(config_obj)
    if request.method == 'POST':
        config_obj.horario_abertura = request.form.get('horario_abertura', '').strip()
        config_obj.horario_fechamento = request.form.get('horario_fechamento', '').strip()
        config_obj.whatsapp_empresa = request.form.get('whatsapp_empresa', '').strip()
        config_obj.entrega_ativa = request.form.get('entrega_ativa') == 'on'
        tempo_espera = request.form.get('tempo_espera_minutos', '').strip() or '35'
        set_param('tempo_espera_minutos', tempo_espera)
        set_param('whatsapp_business_enabled', 'true' if request.form.get('whatsapp_business_enabled') == 'on' else 'false')
        whatsapp_token = request.form.get('whatsapp_business_token', '').strip()
        whatsapp_phone_id = request.form.get('whatsapp_business_phone_id', '').strip()
        whatsapp_api_version = request.form.get('whatsapp_business_api_version', '').strip() or 'v20.0'
        if whatsapp_token:
            set_param('whatsapp_business_token', whatsapp_token)
        if whatsapp_phone_id:
            set_param('whatsapp_business_phone_id', whatsapp_phone_id)
        set_param('whatsapp_business_api_version', whatsapp_api_version)
        set_param('site_theme', request.form.get('site_theme', 'normal'))
        db.session.commit()
        flash('Configuracoes atualizadas.', 'success')
        return redirect(url_for('admin_config'))
    tempo_espera = get_param('tempo_espera_minutos', '35')
    whatsapp_enabled = whatsapp_business_enabled()
    whatsapp_token = get_param('whatsapp_business_token', '')
    whatsapp_phone_id = get_param('whatsapp_business_phone_id', '')
    whatsapp_api_version = get_param('whatsapp_business_api_version', 'v20.0')
    site_theme = get_param('site_theme', 'normal')
    kitchen_printer_enabled = get_param('kitchen_printer_enabled', 'false').lower() == 'true'
    kitchen_printer_name = get_param('kitchen_printer_name', '')
    general_printer_enabled = get_param('general_printer_enabled', 'false').lower() == 'true'
    general_printer_name = get_param('general_printer_name', '')
    return render_template(
        'admin/config.html',
        config_obj=config_obj,
        tempo_espera=tempo_espera,
        whatsapp_enabled=whatsapp_enabled,
        whatsapp_token=whatsapp_token,
        whatsapp_phone_id=whatsapp_phone_id,
        whatsapp_api_version=whatsapp_api_version,
        site_theme=site_theme,
    )


def update_printer_settings_from_form(form):
    set_param('kitchen_printer_enabled', 'true' if form.get('kitchen_printer_enabled') == 'on' else 'false')
    set_param('kitchen_printer_name', form.get('kitchen_printer_name', '').strip())
    set_param('general_printer_enabled', 'true' if form.get('general_printer_enabled') == 'on' else 'false')
    set_param('general_printer_name', form.get('general_printer_name', '').strip())
    set_param('printer_auto_search', 'true' if form.get('printer_auto_search') == 'on' else 'false')


@app.route('/admin/printers', methods=['GET', 'POST'])
@role_required(ROLE_ADMIN)
def admin_printers():
    if request.method == 'POST':
        update_printer_settings_from_form(request.form)
        db.session.commit()
        flash('Configuracoes de impressora atualizadas.', 'success')
        return redirect(url_for('admin_printers'))
    return render_template(
        'admin/printers.html',
        kitchen_printer_enabled=get_param('kitchen_printer_enabled', 'false').lower() == 'true',
        kitchen_printer_name=get_param('kitchen_printer_name', ''),
        general_printer_enabled=get_param('general_printer_enabled', 'false').lower() == 'true',
        general_printer_name=get_param('general_printer_name', ''),
        printer_auto_search=get_param('printer_auto_search', 'false').lower() == 'true',
    )


@app.route('/admin/close-day', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_close_day():
    config_obj = Configuracao.query.first()
    if not config_obj:
        config_obj = Configuracao()
        db.session.add(config_obj)
    config_obj.entrega_ativa = False
    pedidos_para_arquivar = Pedido.query.filter(Pedido.status != 'Arquivado').all()
    for pedido in pedidos_para_arquivar:
        pedido.status = 'Arquivado'
    reset_order_number_counter()
    db.session.commit()
    flash('Delivery fechado. Pedidos removidos do gerenciador e movidos para arquivados.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/open-day', methods=['POST'])
@role_required(ROLE_ADMIN)
def admin_open_day():
    config_obj = Configuracao.query.first()
    if not config_obj:
        config_obj = Configuracao()
        db.session.add(config_obj)
    config_obj.entrega_ativa = True
    db.session.commit()
    flash('Delivery aberto novamente.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delivery/panel')
@role_required(ROLE_DELIVERY)
def delivery_panel():
    entregador_id = session.get('user_id')
    pedidos_ativos = Pedido.query.filter(
        Pedido.entregador_id == entregador_id,
        Pedido.status.in_(['Aceito', 'Em Preparo', 'Saiu para Entrega'])
    ).order_by(Pedido.data.desc()).all()
    historico = Pedido.query.filter(
        Pedido.entregador_id == entregador_id,
        Pedido.status.in_(['Entregue', 'Arquivado'])
    ).order_by(Pedido.data.desc()).limit(20).all()
    taxa_total = sum([float(p.taxa_entrega) for p in historico])
    return render_template('delivery/orders.html', pedidos=pedidos_ativos, historico=historico, taxa_total=taxa_total)


@app.route('/api/products')
def api_products():
    produtos = [p.as_dict() for p in Produto.query.filter_by(ativo=True).all()]
    combos = [c.as_dict() for c in Combo.query.filter_by(ativo=True).all()]
    return jsonify({'produtos': produtos, 'combos': combos})


@app.route('/api/payments')
def api_payments():
    formas = [f.as_dict() for f in FormaPagamento.query.filter_by(ativo=True).order_by(FormaPagamento.nome).all()]
    return jsonify({'formas': formas})


@app.route('/api/session')
def api_session():
    return jsonify({
        'logged_in': bool(session.get('user_id')),
        'role': session.get('user_role'),
        'name': session.get('user_name')
    })


@app.route('/api/theme')
def api_theme():
    return jsonify({'theme': get_param('site_theme', 'normal')})


@app.route('/api/wait-time')
def api_wait_time():
    tempo_espera = get_param('tempo_espera_minutos', '35')
    param = ParametroSistema.query.filter_by(chave='tempo_espera_minutos').first()
    try:
        minutos = int(tempo_espera)
    except ValueError:
        minutos = 35
    return jsonify({
        'tempo_estimado_minutos': minutos,
        'atualizado_em': param.atualizado_em.isoformat() if param and param.atualizado_em else None,
    })


@app.route('/api/client/profile')
def api_client_profile():
    if session.get('user_role') != ROLE_CLIENT or not session.get('user_id'):
        return jsonify({'logged_client': False})
    cliente = Cliente.query.get(session.get('user_id'))
    if not cliente:
        return jsonify({'logged_client': False})
    return jsonify({
        'logged_client': True,
        'nome': cliente.nome,
        'telefone': cliente.telefone,
        'email': cliente.email,
    })


@app.route('/api/coupons/<codigo>')
def api_coupon(codigo):
    cupom = Cupom.query.filter_by(codigo=codigo.upper(), ativo=True).first()
    if cupom and (cupom.limite_uso == 0 or cupom.usado < cupom.limite_uso):
        return jsonify({'valid': True, 'cupom': cupom.as_dict()})
    return jsonify({'valid': False}), 404


@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    config_obj = Configuracao.query.first()
    if config_obj and not config_obj.entrega_ativa:
        return jsonify({'error': 'Delivery fechado no momento.'}), 400

    data = request.get_json() or {}
    nome = data.get('nome', '').strip()
    telefone = data.get('telefone', '').strip()
    endereco = data.get('endereco', '').strip()
    bairro = data.get('bairro', '').strip()
    observacao = data.get('observacao', '').strip()
    forma_pagamento = data.get('forma_pagamento', 'Dinheiro')
    cupom_codigo = data.get('cupom', '').strip().upper() or None
    items = data.get('items', [])
    cliente_id = session.get('user_id') if session.get('user_role') == ROLE_CLIENT else None

    if not nome or not telefone or not endereco or not bairro or not items:
        return jsonify({'error': 'Dados incompletos.'}), 400

    if not cliente_id:
        cliente = Cliente.query.filter_by(telefone=telefone).first()
        if not cliente:
            safe_phone = ''.join(ch for ch in telefone if ch.isdigit()) or str(int(datetime.utcnow().timestamp()))
            guest_email = f"guest_{safe_phone}@toplanches.local"
            email_exists = Cliente.query.filter_by(email=guest_email).first()
            if email_exists:
                guest_email = f"guest_{safe_phone}_{int(datetime.utcnow().timestamp())}@toplanches.local"
            cliente = Cliente(
                nome=nome,
                telefone=telefone,
                email=guest_email,
                senha_hash=generate_password_hash(f'guest-{safe_phone}', method='pbkdf2:sha256', salt_length=12),
                ativo=True
            )
            db.session.add(cliente)
            db.session.flush()
        cliente_id = cliente.id

    forma_ativa = FormaPagamento.query.filter_by(nome=forma_pagamento, ativo=True).first()
    if not forma_ativa:
        return jsonify({'error': 'Forma de pagamento indisponivel.'}), 400

    subtotal = sum([Decimal(str(item['preco'])) * int(item['quantidade']) for item in items])
    taxa_entrega = Decimal(str(get_delivery_fee(bairro)))
    desconto = Decimal('0')

    cupom = None
    if cupom_codigo:
        cupom = Cupom.query.filter_by(codigo=cupom_codigo, ativo=True).first()
        if cupom:
            if cupom.tipo == 'fixo':
                desconto = min(Decimal(str(cupom.valor)), subtotal)
            else:
                desconto = (subtotal * Decimal(str(cupom.valor))) / Decimal('100')
            cupom.usado += 1

    total = subtotal + taxa_entrega - desconto
    pedido = Pedido(
        cliente_id=cliente_id,
        nome=nome,
        telefone=telefone,
        endereco=endereco,
        bairro=bairro,
        observacao=observacao,
        subtotal=subtotal,
        desconto=desconto,
        taxa_entrega=taxa_entrega,
        valor_total=total,
        forma_pagamento=forma_pagamento,
        cupom_aplicado=cupom_codigo,
        status='Pendente',
        data=datetime.utcnow()
    )
    pedido.numero_pedido = get_next_order_number()
    db.session.add(pedido)
    db.session.flush()

    for item in items:
        produto_id = item.get('produto_id')
        combo_id = item.get('combo_id')
        nome_item = item.get('nome')
        quantidade = int(item.get('quantidade', 1))
        valor = Decimal(str(item.get('preco'))) * quantidade
        pedido_item = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto_id,
            combo_id=combo_id,
            nome=nome_item,
            quantidade=quantidade,
            valor=valor
        )
        db.session.add(pedido_item)

    db.session.commit()
    socketio.emit('new_order', {'order_id': pedido.id, 'status': pedido.status})
    return jsonify({'success': True, 'order_id': pedido.id})


@app.route('/api/order/<int:pedido_id>/status', methods=['POST'])
@role_required(ROLE_ADMIN)
def update_order_status(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    status_anterior = pedido.status
    novo_status = request.json.get('status')
    motivo = request.json.get('motivo')
    if novo_status not in ['Pendente', 'Aceito', 'Em Preparo', 'Saiu para Entrega', 'Entregue', 'Recusado']:
        return jsonify({'error': 'Status inválido.'}), 400
    if not can_transition_status(pedido.status, novo_status):
        return jsonify({'error': f'Transição inválida de {pedido.status} para {novo_status}.'}), 400
    novo_status = normalize_next_status(novo_status)
    pedido.status = novo_status
    if novo_status == 'Recusado':
        pedido.motivo_recusa = motivo
    db.session.commit()
    socketio.emit('status_update', {'order_id': pedido.id, 'status': novo_status})
    if status_anterior != novo_status:
        if novo_status == 'Em Preparo':
            notify_order_status(pedido, novo_status, include_summary=True)
        elif novo_status in ['Saiu para Entrega', 'Entregue']:
            notify_order_status(pedido, novo_status)
    return jsonify({'success': True})


@app.route('/api/order/<int:pedido_id>/accept-prepare', methods=['POST'])
@role_required(ROLE_ADMIN)
def accept_prepare_order(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.status != 'Pendente':
        return jsonify({'error': 'Este pedido não pode mais ser aceito.'}), 400
    entregador_id = request.json.get('entregador_id')
    if not entregador_id:
        return jsonify({'error': 'Selecione um entregador.'}), 400
    entregador = Entregador.query.get(entregador_id)
    if not entregador or not entregador.ativo:
        return jsonify({'error': 'Entregador inválido.'}), 400
    pedido.entregador_id = entregador.id
    pedido.status = 'Em Preparo'
    db.session.commit()
    socketio.emit('order_assigned', {'order_id': pedido.id, 'entregador_id': entregador.id})
    socketio.emit('status_update', {'order_id': pedido.id, 'status': pedido.status})
    notify_order_status(pedido, 'Em Preparo', include_summary=True)
    return jsonify({'success': True})


@app.route('/api/delivery/order/<int:pedido_id>/status', methods=['POST'])
@role_required(ROLE_DELIVERY)
def delivery_update_order_status(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if pedido.entregador_id and pedido.entregador_id != session.get('user_id'):
        return jsonify({'error': 'Pedido nao pertence a este entregador.'}), 403
    novo_status = request.json.get('status')
    if novo_status not in ['Saiu para Entrega', 'Entregue']:
        return jsonify({'error': 'Status inválido.'}), 400
    if not can_transition_status(pedido.status, novo_status):
        return jsonify({'error': f'Transição inválida de {pedido.status} para {novo_status}.'}), 400
    pedido.status = novo_status
    db.session.commit()
    socketio.emit('status_update', {'order_id': pedido.id, 'status': novo_status})
    notify_order_status(pedido, novo_status)
    return jsonify({'success': True})


@app.route('/admin/orders/<int:pedido_id>/print-delivery')
@role_required(ROLE_ADMIN)
def print_delivery_ticket(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('admin/print_delivery.html', pedido=pedido)


@app.route('/admin/orders/<int:pedido_id>/print-receipt')
@role_required(ROLE_ADMIN)
def print_store_receipt(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('admin/print_receipt.html', pedido=pedido)


@app.route('/admin/orders/<int:pedido_id>/print-kitchen')
@role_required(ROLE_ADMIN)
def print_kitchen_ticket(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    auto = request.args.get('auto') == '1'
    return render_template('admin/print_kitchen.html', pedido=pedido, auto=auto)


@app.route('/admin/reports/day-invoices')
@role_required(ROLE_ADMIN)
def print_day_invoices():
    today = datetime.utcnow().date()
    pedidos = Pedido.query.filter(func.date(Pedido.data) == today).order_by(Pedido.data.asc()).all()
    return render_template('admin/day_invoices.html', pedidos=pedidos)


@app.route('/api/assign/<int:pedido_id>', methods=['POST'])
@role_required(ROLE_ADMIN)
def assign_delivery(pedido_id):
    entregador_id = request.json.get('entregador_id')
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.entregador_id = entregador_id
    db.session.commit()
    socketio.emit('order_assigned', {'order_id': pedido.id, 'entregador_id': entregador_id})
    return jsonify({'success': True})


@app.route('/api/dashboard')
@role_required(ROLE_ADMIN)
def api_dashboard():
    pedidos = Pedido.query.all()
    return jsonify({
        'totalPedidos': len(pedidos),
        'pendentes': Pedido.query.filter_by(status='Pendente').count(),
        'aceitos': Pedido.query.filter_by(status='Aceito').count(),
        'recusados': Pedido.query.filter_by(status='Recusado').count(),
        'entregues': Pedido.query.filter_by(status='Entregue').count(),
    })


@socketio.on('connect')
def on_connect():
    emit('connected', {'message': 'Conectado ao servidor de pedidos'})


@socketio.on('join_room')
def on_join_room(data):
    room = data.get('room')
    if room:
        join_room(room)


if __name__ == '__main__':
    init_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=config.DEBUG)
