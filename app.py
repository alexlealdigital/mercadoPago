from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Configurações de e-mail (pegando do ambiente)
EMAIL_CONFIG = {
    "from": os.getenv("EMAIL_SENDER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "smtp_server": os.getenv("SMTP_SERVER"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587))  # Default para 587 se não definido
}

def send_download_links(email: str, payment_id: str):
    """Envia e-mail com links de download"""
    if not email:
        print("Erro: E-mail do comprador não disponível")
        return
        
    msg = EmailMessage()
    msg['Subject'] = "✅ Seu download está pronto!"
    msg['From'] = EMAIL_CONFIG['from']
    msg['To'] = email
    
    msg.set_content(f"""
    Obrigado por sua compra! (#{payment_id})
    
    📥 Links para download:
    - Produto 1: https://exemplo.com/download/{payment_id}/produto1
    - Produto 2: https://exemplo.com/download/{payment_id}/produto2
    
    ⏳ Links válidos por 7 dias.
    """)
    
    try:
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['from'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        print(f"E-mail enviado para {email}")
    except Exception as e:
        print(f"Falha ao enviar e-mail: {str(e)}")

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Mercado Pago Webhook"})

@app.route('/webhook', methods=['POST', 'GET'])
def handle_webhook():
    try:
        # Verifica o formato dos dados (query params ou JSON)
        if request.method == 'GET':
            payment_id = request.args.get('data.id')
            notification_type = request.args.get('type')
        else:
            data = request.get_json()
            payment_id = data.get('data', {}).get('id')
            notification_type = data.get('type')

        if not payment_id or notification_type != 'payment':
            return jsonify({"error": "Invalid request"}), 400

        # Consulta completa na API do Mercado Pago
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        payment_info = sdk.payment().get(payment_id)
        
        if payment_info['response']['status'] == 'approved':
            send_download_links(
                email=payment_info['response']['payer']['email'],
                payment_id=payment_id
            )

        return jsonify({"status": "processed"}), 200

    except Exception as e:
        app.logger.error(f"Erro: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Endpoint para verificar se o servidor está online"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Use 10000 para compatibilidade com Render
    app.run(host='0.0.0.0', port=port)
