# Online Menu

O sistema de gerar pedidos não está com redirecionamento do pedido para o WhatsApp, pois não tenho um núnero de referência.

Projeto no figma:
https://www.figma.com/file/zFC4MoN5y14YFafXLbF2oM/Home?node-id=0%3A1

## Tecnologias utilizadas
* Python Flask
* MySQL
* WebSocket (Flask-SocketIO)
* HTML5
* CSS3
* JavaScript
* ToastifyJS

## Novo fluxo do sistema
* Backend Flask integrado ao MySQL
* Painel administrativo, cliente e entregador
* Catálogo de produtos e combos
* Carrinho de compras com cupom, entrega e pagamento
* Pedidos salvos no banco com histórico e status
* Atualizações em tempo real via WebSocket

## Como rodar localmente
1. Copie `.env.example` para `.env`.
2. Ajuste as credenciais MySQL.
3. Instale dependências:

```bash
pip install -r requirements.txt
```

4. Crie o banco de dados ou use `schema.sql`.
5. Execute:

```bash
python app.py
```

O servidor ficará disponível em `http://127.0.0.1:5000`.
