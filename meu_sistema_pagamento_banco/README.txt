# Sistema de Pagamento com Banco de Dados

## Como usar

1. Preencha o arquivo `.env` com seus dados reais de Mercado Pago e Render (PostgreSQL).
2. Instale as dependências com:

   pip install -r requirements.txt

3. Execute o app:

   python app.py

4. Acesse `http://localhost:5000` para usar o formulário e testar pagamentos.

5. A rota /notificacao receberá a confirmação do Mercado Pago e gravará no banco.
