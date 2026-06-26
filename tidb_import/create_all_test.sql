-- Top LanchesBG
-- Cria todas as tabelas no schema test
-- Execute este arquivo inteiro no TiDB Cloud

CREATE TABLE IF NOT EXISTS test.configuracoes (
  id INT NOT NULL AUTO_INCREMENT,
  horario_abertura VARCHAR(50) NULL,
  horario_fechamento VARCHAR(50) NULL,
  whatsapp_empresa VARCHAR(80) NULL,
  taxa_fixa DECIMAL(10,2) DEFAULT 0.00,
  entrega_ativa TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.usuarios (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  usuario VARCHAR(80) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  nivel VARCHAR(30) NOT NULL DEFAULT 'admin',
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuarios_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.clientes (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(30) NOT NULL,
  email VARCHAR(120) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_clientes_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.entregadores (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(30) NOT NULL,
  usuario VARCHAR(80) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_entregadores_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.produtos (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(160) NOT NULL,
  descricao TEXT NULL,
  preco DECIMAL(10,2) NOT NULL,
  imagem VARCHAR(255) NULL,
  estoque INT DEFAULT 0,
  categoria VARCHAR(80) NULL,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.combos (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(160) NOT NULL,
  descricao TEXT NULL,
  preco DECIMAL(10,2) NOT NULL,
  imagem VARCHAR(255) NULL,
  ativo TINYINT(1) DEFAULT 1,
  validade DATETIME NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.cupons (
  id INT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(60) NOT NULL,
  tipo ENUM('fixo', 'percentual') NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  validade DATETIME NULL,
  limite_uso INT DEFAULT 1,
  usado INT DEFAULT 0,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cupons_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.banners (
  id INT NOT NULL AUTO_INCREMENT,
  titulo VARCHAR(160) NOT NULL,
  descricao TEXT NULL,
  imagem VARCHAR(255) NULL,
  validade DATETIME NULL,
  ativo TINYINT(1) DEFAULT 1,
  prioridade INT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.formas_pagamento (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  descricao VARCHAR(255) NULL,
  ativo TINYINT(1) DEFAULT 1,
  aceita_troco TINYINT(1) DEFAULT 0,
  valor_troco DECIMAL(10,2) DEFAULT 0.00,
  chave_pix VARCHAR(255) NULL,
  qr_code VARCHAR(255) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.taxas_entrega (
  id INT NOT NULL AUTO_INCREMENT,
  bairro VARCHAR(120) NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.pedidos (
  id INT NOT NULL AUTO_INCREMENT,
  numero_pedido INT NULL,
  cliente_id INT NOT NULL,
  entregador_id INT NULL,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(30) NOT NULL,
  endereco VARCHAR(255) NOT NULL,
  bairro VARCHAR(120) NOT NULL,
  observacao TEXT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  desconto DECIMAL(10,2) DEFAULT 0.00,
  taxa_entrega DECIMAL(10,2) NOT NULL,
  valor_total DECIMAL(10,2) NOT NULL,
  forma_pagamento VARCHAR(120) NOT NULL,
  cupom_aplicado VARCHAR(60) NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Pendente',
  data DATETIME DEFAULT CURRENT_TIMESTAMP,
  motivo_recusa VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_pedidos_cliente_id (cliente_id),
  KEY idx_pedidos_entregador_id (entregador_id),
  CONSTRAINT fk_pedidos_cliente FOREIGN KEY (cliente_id) REFERENCES test.clientes (id),
  CONSTRAINT fk_pedidos_entregador FOREIGN KEY (entregador_id) REFERENCES test.entregadores (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.itens_pedido (
  id INT NOT NULL AUTO_INCREMENT,
  pedido_id INT NOT NULL,
  produto_id INT NULL,
  combo_id INT NULL,
  nome VARCHAR(160) NOT NULL,
  quantidade INT NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_itens_pedido_pedido_id (pedido_id),
  KEY idx_itens_pedido_produto_id (produto_id),
  KEY idx_itens_pedido_combo_id (combo_id),
  CONSTRAINT fk_itens_pedido_pedido FOREIGN KEY (pedido_id) REFERENCES test.pedidos (id) ON DELETE CASCADE,
  CONSTRAINT fk_itens_pedido_produto FOREIGN KEY (produto_id) REFERENCES test.produtos (id),
  CONSTRAINT fk_itens_pedido_combo FOREIGN KEY (combo_id) REFERENCES test.combos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.parametros_sistema (
  id INT NOT NULL AUTO_INCREMENT,
  chave VARCHAR(80) NOT NULL,
  valor VARCHAR(255) NOT NULL,
  atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_parametros_sistema_chave (chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS test.historico_alteracoes (
  id INT NOT NULL AUTO_INCREMENT,
  entidade VARCHAR(80) NOT NULL,
  item_id INT NULL,
  item_nome VARCHAR(160) NOT NULL,
  campo VARCHAR(80) NOT NULL,
  valor_antigo VARCHAR(255) NULL,
  valor_novo VARCHAR(255) NULL,
  alterado_por VARCHAR(120) NOT NULL,
  alterado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
