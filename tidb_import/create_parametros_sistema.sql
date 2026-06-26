CREATE TABLE IF NOT EXISTS test.parametros_sistema (
  id INT NOT NULL AUTO_INCREMENT,
  chave VARCHAR(80) NOT NULL,
  valor VARCHAR(255) NOT NULL,
  atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_parametros_sistema_chave (chave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO test.parametros_sistema (chave, valor)
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
