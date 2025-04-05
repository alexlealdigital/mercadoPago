from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage
import logging
import mercadopago

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

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        # Verifica autenticação
        if request.headers.get('Authorization') != f"Bearer {os.getenv('WEBHOOK_TOKEN')}":
            return jsonify({"error": "Unauthorized"}), 401

        # Processa dados do webhook
        data = request.get_json()
        payment_id = data.get('data', {}).get('id')
        if not payment_id:
            return jsonify({"error": "Payment ID missing"}), 400

        # Consulta API do Mercado Pago
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        payment_info = sdk.payment().get(payment_id)
        
        # Verificação robusta da resposta
        if not payment_info or 'response' not in payment_info:
            app.logger.error("Resposta inválida da API MP: %s", payment_info)
            return jsonify({"error": "Invalid MP API response"}), 502
            
        payment_data = payment_info.get('response', {})
        
        if payment_data.get('status') == 'approved':
            email = payment_data.get('payer', {}).get('email')
            if email:
                send_download_links(email, payment_id)
                return jsonify({"status": "processed"}), 200
            return jsonify({"error": "Payer email missing"}), 400
            
        return jsonify({"status": "payment_not_approved"}), 200

    except Exception as e:
        app.logger.error("Erro crítico: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
        
@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
