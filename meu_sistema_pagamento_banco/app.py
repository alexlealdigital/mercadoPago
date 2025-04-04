from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Endpoint que recebe as notificações do Mercado Pago
@app.route('/webhook', methods=['POST'])
def webhook():
    # Verificar o token de autenticação se necessário
    auth_token = request.headers.get('Authorization')
    # if auth_token != os.getenv('WEBHOOK_TOKEN'):
    #     return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    # Extrair informações importantes
    payment_id = data.get('data', {}).get('id')
    payment_status = data.get('action')  # Ex: 'payment.created', 'payment.updated'
    payer_email = data.get('data', {}).get('payer', {}).get('email')
    
    print(f"Recebido webhook: {payment_status} - Email: {payer_email}")
    
    if payment_id and payment_status == 'payment.updated':
        # Aqui você pode adicionar sua lógica para verificar se o pagamento foi aprovado
        # e enviar os e-mails com os links de download
        print(f"Pagamento {payment_id} atualizado. Status: {data.get('data', {}).get('status')}")
        if data.get('data', {}).get('status') == 'approved':
            send_download_links(payer_email, payment_id)
    
    return jsonify({"status": "received"}), 200

def send_download_links(email, payment_id):
    # Implemente o envio de e-mail aqui
    print(f"Enviando links de download para: {email} - Pagamento ID: {payment_id}")
    # Exemplo simplificado:
    # msg = f"Obrigado por sua compra! Seus links de download: [LINKS AQUI]"
    # enviar_email(email, "Seus downloads", msg)

@app.route('/')
def home():
    return "Webhook do Mercado Pago está rodando!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
