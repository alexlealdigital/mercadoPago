from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage
import logging
import mercadopago
from dotenv import load_dotenv
load_dotenv('/etc/secrets/.env')  # Caminho padrão no Render

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Timeout configuration
@app.before_request
def handle_timeout():
    request.environ['werkzeug.server.shutdown'] = lambda: None
    request.environ['werkzeug.socket'] = None

# Email configuration from environment variables
EMAIL_CONFIG = {
    "from": os.getenv("EMAIL_SENDER", "lab.leal.jornal@zohomail.com"),
    "password": os.getenv("EMAIL_PASSWORD", "Chat2025$"),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.zoho.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587))
}

def send_download_links(email: str, payment_id: str):
    """Send email with download links"""
    if not email:
        logger.error("No email provided")
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
        logger.info(f"Email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

@app.route('/')
def home():
    return jsonify({
        "service": "Mercado Pago Webhook",
        "status": "online",
        "version": "1.0"
    })

# Exemplo de modificação para melhorar a segurança
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    app.logger.info("Headers recebidos: %s", request.headers)
    app.logger.info("Payload recebido: %s", request.json)
    
    auth_header = request.headers.get('Authorization')
    expected = f"Bearer {os.getenv('WEBHOOK_TOKEN')}"
    
    if not auth_header or auth_header != expected:
        app.logger.error("Token inválido. Recebido: %s | Esperado: %s", auth_header, expected)
        return jsonify({"error": "Unauthorized"}), 401
    
    # Resto do seu código...

    # Validação do payload
    data = request.get_json()
    if not data.get('data', {}).get('id'):
        return jsonify({"error": "Payment ID missing"}), 400

    # Consulta API MP (com timeout)
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
    try:
        payment_info = sdk.payment().get(data['data']['id'], timeout=10)
        if payment_info['response']['status'] == 'approved':
            send_download_links(payment_info['response']['payer']['email'], data['data']['id'])
            return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Erro na API MP: {str(e)}")
        return jsonify({"error": "MP API error"}), 500
       
        
@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
