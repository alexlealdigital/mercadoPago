from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage
import logging
import mercadopago
import hmac
import hashlib
from functools import wraps
from dotenv import load_dotenv

load_dotenv('/etc/secrets/.env')  # Caminho padrão no Render

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações do Mercado Pago
MP_WEBHOOK_TOKEN = os.getenv("MP_WEBHOOK_TOKEN")  # Token específico para webhooks
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")    # Access token para API

# Email configuration from environment variables
EMAIL_CONFIG = {
    "from": os.getenv("EMAIL_SENDER", "lab.leal.jornal@zohomail.com"),
    "password": os.getenv("EMAIL_PASSWORD", "Chat2025$"),
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.zoho.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", 587))
}

def verify_mp_signature(request):
    """Valida a assinatura no formato do Mercado Pago (ts=...,v1=...)"""
    signature_header = request.headers.get("X-Signature", "")
    if not signature_header or not MP_WEBHOOK_TOKEN:
        return False

    try:
        # Extrai a assinatura v1 do header (formato: "ts=123,v1=hash")
        parts = dict(p.split("=") for p in signature_header.split(","))
        received_signature = parts.get("v1", "")
    except Exception:
        return False

    # Calcula o hash esperado
    expected_signature = hmac.new(
        MP_WEBHOOK_TOKEN.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(received_signature, expected_signature)

def mp_webhook_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not verify_mp_signature(request):
            logger.error(f"Assinatura inválida. Recebido: {request.headers.get('X-Signature')} | Esperado: Bearer {MP_WEBHOOK_TOKEN}")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

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
@mp_webhook_required
def handle_webhook():
    try:
        logger.info("Headers recebidos: %s", request.headers)
        logger.info("Payload recebido: %s", request.json)
        
        # Validação do payload
        data = request.get_json()
        if not data.get('data', {}).get('id'):
            return jsonify({"error": "Payment ID missing"}), 400

        # Consulta API MP (com timeout)
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        payment_info = sdk.payment().get(data['data']['id'], timeout=10)
        
        if payment_info['response']['status'] == 'approved':
            email = payment_info['response']['payer']['email']
            send_download_links(email, data['data']['id'])
            return jsonify({"status": "success"}), 200
        
        return jsonify({"status": "payment_not_approved"}), 200

    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
       
@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
