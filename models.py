from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    nivel = db.Column(db.String(30), nullable=False, default='admin')
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'usuario': self.usuario,
            'nivel': self.nivel,
            'ativo': self.ativo,
        }

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'ativo': self.ativo,
        }

class Entregador(db.Model):
    __tablename__ = 'entregadores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'usuario': self.usuario,
            'ativo': self.ativo,
        }

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    imagem = db.Column(db.String(255), nullable=True)
    estoque = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(80), nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco),
            'imagem': self.imagem,
            'estoque': self.estoque,
            'categoria': self.categoria,
            'ativo': self.ativo,
        }

class Combo(db.Model):
    __tablename__ = 'combos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    imagem = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    validade = db.Column(db.DateTime, nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco),
            'imagem': self.imagem,
            'ativo': self.ativo,
            'validade': self.validade.isoformat() if self.validade else None,
        }

class Cupom(db.Model):
    __tablename__ = 'cupons'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(60), unique=True, nullable=False)
    tipo = db.Column(db.Enum('fixo', 'percentual'), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    validade = db.Column(db.DateTime, nullable=True)
    limite_uso = db.Column(db.Integer, default=1)
    usado = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'tipo': self.tipo,
            'valor': float(self.valor),
            'validade': self.validade.isoformat() if self.validade else None,
            'limite_uso': self.limite_uso,
            'usado': self.usado,
            'ativo': self.ativo,
        }

class Banner(db.Model):
    __tablename__ = 'banners'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    imagem = db.Column(db.String(255), nullable=True)
    validade = db.Column(db.DateTime, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    prioridade = db.Column(db.Integer, default=1)

    def as_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'imagem': self.imagem,
            'validade': self.validade.isoformat() if self.validade else None,
            'ativo': self.ativo,
            'prioridade': self.prioridade,
        }

class FormaPagamento(db.Model):
    __tablename__ = 'formas_pagamento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    aceita_troco = db.Column(db.Boolean, default=False)
    valor_troco = db.Column(db.Numeric(10, 2), default=0)
    chave_pix = db.Column(db.String(255), nullable=True)
    qr_code = db.Column(db.String(255), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo,
            'aceita_troco': self.aceita_troco,
            'valor_troco': float(self.valor_troco),
            'chave_pix': self.chave_pix,
            'qr_code': self.qr_code,
        }

class TaxaEntrega(db.Model):
    __tablename__ = 'taxas_entrega'
    id = db.Column(db.Integer, primary_key=True)
    bairro = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'bairro': self.bairro,
            'valor': float(self.valor),
            'ativo': self.ativo,
        }

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.Integer, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    entregador_id = db.Column(db.Integer, db.ForeignKey('entregadores.id'), nullable=True)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    bairro = db.Column(db.String(120), nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    desconto = db.Column(db.Numeric(10, 2), default=0)
    taxa_entrega = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(120), nullable=False)
    cupom_aplicado = db.Column(db.String(60), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pendente')
    data = db.Column(db.DateTime, default=datetime.utcnow)
    motivo_recusa = db.Column(db.String(255), nullable=True)

    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)

    def as_dict(self):
        return {
            'id': self.id,
            'numero_pedido': self.numero_pedido,
            'cliente_id': self.cliente_id,
            'entregador_id': self.entregador_id,
            'nome': self.nome,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'bairro': self.bairro,
            'observacao': self.observacao,
            'subtotal': float(self.subtotal),
            'desconto': float(self.desconto),
            'taxa_entrega': float(self.taxa_entrega),
            'valor_total': float(self.valor_total),
            'forma_pagamento': self.forma_pagamento,
            'cupom_aplicado': self.cupom_aplicado,
            'status': self.status,
            'data': self.data.isoformat(),
            'motivo_recusa': self.motivo_recusa,
            'itens': [item.as_dict() for item in self.itens],
        }

class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    combo_id = db.Column(db.Integer, db.ForeignKey('combos.id'), nullable=True)
    nome = db.Column(db.String(160), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)

    def as_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'produto_id': self.produto_id,
            'combo_id': self.combo_id,
            'nome': self.nome,
            'quantidade': self.quantidade,
            'valor': float(self.valor),
        }

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    id = db.Column(db.Integer, primary_key=True)
    horario_abertura = db.Column(db.String(50), nullable=True)
    horario_fechamento = db.Column(db.String(50), nullable=True)
    whatsapp_empresa = db.Column(db.String(80), nullable=True)
    taxa_fixa = db.Column(db.Numeric(10, 2), default=0)
    entrega_ativa = db.Column(db.Boolean, default=True)

    def as_dict(self):
        return {
            'id': self.id,
            'horario_abertura': self.horario_abertura,
            'horario_fechamento': self.horario_fechamento,
            'whatsapp_empresa': self.whatsapp_empresa,
            'taxa_fixa': float(self.taxa_fixa),
            'entrega_ativa': self.entrega_ativa,
        }


class ParametroSistema(db.Model):
    __tablename__ = 'parametros_sistema'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(80), unique=True, nullable=False)
    valor = db.Column(db.String(255), nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def as_dict(self):
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': self.valor,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
        }


class HistoricoAlteracao(db.Model):
    __tablename__ = 'historico_alteracoes'
    id = db.Column(db.Integer, primary_key=True)
    entidade = db.Column(db.String(80), nullable=False)
    item_id = db.Column(db.Integer, nullable=True)
    item_nome = db.Column(db.String(160), nullable=False)
    campo = db.Column(db.String(80), nullable=False)
    valor_antigo = db.Column(db.String(255), nullable=True)
    valor_novo = db.Column(db.String(255), nullable=True)
    alterado_por = db.Column(db.String(120), nullable=False)
    alterado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        return {
            'id': self.id,
            'entidade': self.entidade,
            'item_id': self.item_id,
            'item_nome': self.item_nome,
            'campo': self.campo,
            'valor_antigo': self.valor_antigo,
            'valor_novo': self.valor_novo,
            'alterado_por': self.alterado_por,
            'alterado_em': self.alterado_em.isoformat() if self.alterado_em else None,
        }
