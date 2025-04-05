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

@app.route('/webhook', methods=['GET', 'POST'])
def handle_webhook():
    try:
        # Support both GET (query params) and POST (JSON)
        if request.method == 'GET':
            payment_id = request.args.get('data.id')
            if not payment_id:
                logger.warning("Missing payment ID in GET request")
                return jsonify({"error": "Missing payment ID"}), 400
        else:
            data = request.get_json()
            payment_id = data.get('data', {}).get('id')
            if not payment_id:
                logger.warning("Invalid JSON payload")
                return jsonify({"error": "Invalid JSON payload"}), 400

        # Initialize MP SDK
        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        
        # Get payment details from MP API
        payment_info = sdk.payment().get(payment_id)
        if not payment_info or 'response' not in payment_info:
            logger.error("Failed to get payment info from MP API")
            return jsonify({"error": "Payment not found"}), 404
            
        if payment_info['response']['status'] == 'approved':
            email = payment_info['response']['payer']['email']
            logger.info(f"Processing approved payment {payment_id} for {email}")
            send_download_links(email, payment_id)
        
        return jsonify({"status": "processed"}), 200

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
