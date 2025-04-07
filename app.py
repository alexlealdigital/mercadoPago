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

# Carrega variáveis de ambiente - ATENÇÃO AO CAMINHO
env_path = '/etc/secrets/.env' if os.path.exists('/etc/secrets/.env') else '.env'
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações MP (OBRIGATÓRIAS no Render.com)
MP_WEBHOOK_TOKEN = os.environ['MP_WEBHOOK_TOKEN']  # Isso vai falhar se não estiver configurado
MP_ACCESS_TOKEN = os.environ['MP_ACCESS_TOKEN']

# ... (mantenha suas configurações de email existentes) ...

def verify_mp_signature(request):
    """Validação CORRETA para o formato atual do Mercado Pago"""
    try:
        signature_header = request.headers.get("X-Signature")
        if not signature_header:
            logger.error("Header X-Signature ausente")
            return False
            
        # Extrai a parte v1 da assinatura (formato "ts=...,v1=...")
        signature_parts = dict(p.split("=") for p in signature_header.split(","))
        received_signature = signature_parts.get("v1", "")
        
        # Gera a assinatura esperada
        generated_signature = hmac.new(
            MP_WEBHOOK_TOKEN.encode('utf-8'),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        # Comparação segura
        return hmac.compare_digest(received_signature, generated_signature)
        
    except Exception as e:
        logger.error(f"Erro na verificação: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # 1. Verificação da assinatura
    if not verify_mp_signature(request):
        logger.error(f"Token config: {MP_WEBHOOK_TOKEN[:2]}...{MP_WEBHOOK_TOKEN[-2:]}")
        return jsonify({"error": "Assinatura inválida"}), 401
    
    # 2. Processamento do payload
    try:
        data = request.json
        logger.info(f"Payload válido recebido: {data}")
        
        # ... (seu código existente de processamento) ...
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return jsonify({"error": "Erro interno"}), 500

# ... (mantenha o resto do seu código) ...
@app.route('/healthcheck', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
