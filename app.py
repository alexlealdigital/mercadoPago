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

# Caminho padrão do Render para Secret Files
SECRETS_DIR = '/etc/secrets/'

def load_secret(filename):
    try:
        with open(os.path.join(SECRETS_DIR, filename), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Carrega as variáveis
MP_WEBHOOK_TOKEN = load_secret('MP_WEBHOOK_TOKEN') or os.getenv('MP_WEBHOOK_TOKEN')
MP_ACCESS_TOKEN = load_secret('MP_ACCESS_TOKEN') or os.getenv('MP_ACCESS_TOKEN')

# Verificação
if not MP_WEBHOOK_TOKEN or not MP_ACCESS_TOKEN:
    raise RuntimeError(
        "Tokens MP não configurados! "
        "Adicione MP_WEBHOOK_TOKEN e MP_ACCESS_TOKEN "
        "como Environment Variables OU Secret Files no Render.com"
    )

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

@app.route('/check-config')
def check_config():
    return jsonify({
        'webhook_token_loaded': bool(MP_WEBHOOK_TOKEN),
        'access_token_loaded': bool(MP_ACCESS_TOKEN),
        'loading_method': 'Secret Files' if os.path.exists(SECRETS_DIR) else 'Environment Variables'
    })

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
