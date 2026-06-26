# Importacao rapida no TiDB Cloud

## Arquivos
- parametros_sistema.csv
- configuracoes.csv
- formas_pagamento.csv
- usuarios.csv
- create_parametros_sistema.sql

## Passo 1 (corrigir erro atual)
1. Abra o SQL Editor do TiDB Cloud no database alvo.
2. Rode o arquivo create_parametros_sistema.sql.

Isso resolve o erro: Table '<database>.parametros_sistema' doesn't exist.

## Passo 2 (importar CSV)
1. No TiDB Cloud, use Import -> CSV.
2. Importe cada arquivo para a tabela correspondente:
   - parametros_sistema.csv -> parametros_sistema
   - configuracoes.csv -> configuracoes
   - formas_pagamento.csv -> formas_pagamento
   - usuarios.csv -> usuarios
3. Se a tabela nao existir, escolha opcao de criar tabela pelo arquivo CSV.

## Observacao importante
Nao use o schema de sistema `sys` para aplicacao se puder evitar.
Se possivel, crie um database proprio (exemplo: toplanches) e aponte DB_NAME para ele.
