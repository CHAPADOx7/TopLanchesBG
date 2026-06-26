-- Top LanchesBG
-- Schema inicial para MySQL / MariaDB
-- Compatível com o projeto atual em Flask + SQLAlchemy

CREATE DATABASE IF NOT EXISTS toplanches
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE toplanches;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS historico_alteracoes;
DROP TABLE IF EXISTS parametros_sistema;
DROP TABLE IF EXISTS itens_pedido;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS taxas_entrega;
DROP TABLE IF EXISTS formas_pagamento;
DROP TABLE IF EXISTS banners;
DROP TABLE IF EXISTS cupons;
DROP TABLE IF EXISTS combos;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS entregadores;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS configuracoes;

CREATE TABLE configuracoes (
  id INT NOT NULL AUTO_INCREMENT,
  horario_abertura VARCHAR(50) NULL,
  horario_fechamento VARCHAR(50) NULL,
  whatsapp_empresa VARCHAR(80) NULL,
  taxa_fixa DECIMAL(10,2) DEFAULT 0.00,
  entrega_ativa TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE usuarios (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  usuario VARCHAR(80) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  nivel VARCHAR(30) NOT NULL DEFAULT 'admin',
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuarios_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE clientes (
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

CREATE TABLE entregadores (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(30) NOT NULL,
  usuario VARCHAR(80) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_entregadores_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE produtos (
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

CREATE TABLE combos (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(160) NOT NULL,
  descricao TEXT NULL,
  preco DECIMAL(10,2) NOT NULL,
  imagem VARCHAR(255) NULL,
  ativo TINYINT(1) DEFAULT 1,
  validade DATETIME NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cupons (
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

CREATE TABLE banners (
  id INT NOT NULL AUTO_INCREMENT,
  titulo VARCHAR(160) NOT NULL,
  descricao TEXT NULL,
  imagem VARCHAR(255) NULL,
  validade DATETIME NULL,
  ativo TINYINT(1) DEFAULT 1,
  prioridade INT DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE formas_pagamento (
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

CREATE TABLE taxas_entrega (
  id INT NOT NULL AUTO_INCREMENT,
  bairro VARCHAR(120) NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  ativo TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE pedidos (
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
  CONSTRAINT fk_pedidos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id),
  CONSTRAINT fk_pedidos_entregador FOREIGN KEY (entregador_id) REFERENCES entregadores (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE itens_pedido (
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
  CONSTRAINT fk_itens_pedido_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
  CONSTRAINT fk_itens_pedido_produto FOREIGN KEY (produto_id) REFERENCES produtos (id),
  CONSTRAINT fk_itens_pedido_combo FOREIGN KEY (combo_id) REFERENCES combos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE parametros_sistema (
  id INT NOT NULL AUTO_INCREMENT,
  chave VARCHAR(80) NOT NULL,
  valor VARCHAR(255) NOT NULL,
  atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_parametros_sistema_chave (chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE historico_alteracoes (
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

INSERT INTO configuracoes (id, horario_abertura, horario_fechamento, whatsapp_empresa, taxa_fixa, entrega_ativa)
VALUES (1, '17:00', '00:00', '552299568835', 5.00, 1);

INSERT INTO usuarios (id, nome, usuario, senha_hash, nivel, ativo)
VALUES (
  1,
  'Administrador Top LanchesBG',
  'topbgadmin26',
  'pbkdf2:sha256:600000$8Tzw3LaMINXM$1c418071c3e63a85d4e225ce282a1c15878a237bb25f5494322a4ea3c1baca9f',
  'admin',
  1
);

INSERT INTO formas_pagamento (nome, descricao, ativo, aceita_troco, valor_troco)
VALUES
  ('Dinheiro em especie', 'Pagamento em dinheiro', 1, 1, 0.00),
  ('Cartao de credito', 'Credito', 1, 0, 0.00),
  ('Cartao de debito', 'Debito', 1, 0, 0.00),
  ('PIX', 'Pagamento instantaneo', 1, 0, 0.00),
  ('Outras', 'Voucher e outros', 1, 0, 0.00);

INSERT INTO parametros_sistema (chave, valor)
VALUES
  ('tempo_espera_minutos', '35'),
  ('pedido_ordem_atual', '0'),
  ('kitchen_printer_enabled', 'false'),
  ('kitchen_printer_name', ''),
  ('general_printer_enabled', 'false'),
  ('general_printer_name', ''),
  ('site_theme', 'normal'),
  ('printer_auto_search', 'false')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);

SET FOREIGN_KEY_CHECKS = 1;

-- Credenciais iniciais do admin:
-- usuario: topbgadmin26
-- senha: bg2k26s2.
