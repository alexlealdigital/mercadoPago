from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage
import logging
import mercadopago
import hmac
import hashlib
from functools import wraps

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do Flask
app = Flask(__name__)

# Configuração de caminhos para secrets
SECRETS_DIR = '/etc/secrets/'

def load_secret(filename):
    """Carrega variáveis secretas tanto do Render quanto de arquivos .env"""
    try:
        # Tenta carregar do Secret Files do Render
        secret_path = os.path.join(SECRETS_DIR, filename)
        if os.path.exists(secret_path):
            with open(secret_path, 'r') as f:
                return f.read().strip()
        
        # Tenta carregar de variáveis de ambiente tradicionais
        return os.environ[filename]
    
    except Exception as e:
        logger.error(f"Erro ao carregar secret {filename}: {str(e)}")
        return None

# Carregamento das variáveis críticas
try:
    MP_WEBHOOK_TOKEN = load_secret('MP_WEBHOOK_TOKEN')
    MP_ACCESS_TOKEN = load_secret('MP_ACCESS_TOKEN')
    
    if not MP_WEBHOOK_TOKEN or not MP_ACCESS_TOKEN:
        raise RuntimeError("Tokens MP não configurados corretamente")
        
except Exception as e:
    logger.critical(f"Falha ao carregar configurações: {str(e)}")
    raise

# Configuração de e-mail
EMAIL_CONFIG = {
    "from": load_secret('EMAIL_SENDER') or "lab.leal.jornal@zohomail.com",
    "password": load_secret('EMAIL_PASSWORD') or "Chat2025$",
    "smtp_server": load_secret('SMTP_SERVER') or "smtp.zoho.com",
    "smtp_port": int(load_secret('SMTP_PORT') or 587)
}

# SDK Mercado Pago
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

def verify_mp_signature(request):
    """Valida a assinatura do webhook do Mercado Pago"""
    try:
        signature_header = request.headers.get("X-Signature")
        if not signature_header:
            logger.error("Header X-Signature ausente")
            return False
            
        # Extrai a assinatura (formato "ts=...,v1=...")
        signature_parts = dict(p.split("=") for p in signature_header.split(","))
        received_signature = signature_parts.get("v1", "")
        
        # Gera a assinatura esperada
        expected_signature = hmac.new(
            MP_WEBHOOK_TOKEN.encode('utf-8'),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Erro na verificação de assinatura: {str(e)}")
        return False

def send_download_links(email: str, payment_id: str):
    """Envia e-mail com links de download"""
    if not email:
        logger.error("Nenhum e-mail fornecido para envio")
        return False
        
    try:
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
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['from'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        
        logger.info(f"E-mail enviado para {email}")
        return True
        
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail: {str(e)}")
        return False

@app.route('/')
def home():
    return jsonify({
        "service": "Mercado Pago Webhook",
        "status": "online",
        "version": "1.0"
    })

@app.route('/check-config')
def check_config():
    """Endpoint para verificar configuração"""
    return jsonify({
        'webhook_token_loaded': bool(MP_WEBHOOK_TOKEN),
        'access_token_loaded': bool(MP_ACCESS_TOKEN),
        'email_configured': all(EMAIL_CONFIG.values()),
        'loading_method': 'Secret Files' if os.path.exists(SECRETS_DIR) else 'Environment Variables'
    })

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Endpoint principal para webhooks do Mercado Pago"""
    # 1. Verificação de assinatura
    if not verify_mp_signature(request):
        logger.error("Assinatura inválida recebida")
        return jsonify({"error": "Assinatura inválida"}), 401
    
    # 2. Processamento do payload
    try:
        data = request.json
        logger.info(f"Webhook recebido: {data}")
        
        # Verifica se é um pagamento aprovado
        if data.get('action') == 'payment.updated' and data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if not payment_id:
                return jsonify({"error": "ID de pagamento ausente"}), 400
            
            # Consulta detalhes do pagamento
            payment_info = sdk.payment().get(payment_id)
            if payment_info['response']['status'] == 'approved':
                email = payment_info['response']['payer']['email']
                if send_download_links(email, payment_id):
                    return jsonify({"status": "success"}), 200
                return jsonify({"error": "Falha ao enviar e-mail"}), 500
        
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return jsonify({"error": "Erro interno"}), 500

@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
