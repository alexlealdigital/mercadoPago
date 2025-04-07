from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import logging

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregamento das variáveis
WEBHOOK_TOKEN = os.getenv('MP_WEBHOOK_TOKEN')
ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN')

if not WEBHOOK_TOKEN or not ACCESS_TOKEN:
    logger.error("Variáveis de ambiente não configuradas corretamente!")
    raise RuntimeError("Configure MP_WEBHOOK_TOKEN e MP_ACCESS_TOKEN")

def verify_signature(request):
    """Validação robusta da assinatura do webhook"""
    try:
        signature_header = request.headers.get('X-Signature')
        if not signature_header:
            logger.error("Header X-Signature ausente")
            return False
        
        # Extrai a parte v1 da assinatura
        signature_parts = dict(p.split("=") for p in signature_header.split(","))
        received_hash = signature_parts.get("v1", "")
        
        # Gera a assinatura esperada
        expected_hash = hmac.new(
            WEBHOOK_TOKEN.encode('utf-8'),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        # Comparação segura
        if not hmac.compare_digest(received_hash, expected_hash):
            logger.error(f"Assinatura inválida. Recebido: {received_hash[:6]}... | Esperado: {expected_hash[:6]}...")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Erro na verificação: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # 1. Validação da assinatura
    if not verify_signature(request):
        return jsonify({"error": "Assinatura inválida"}), 401
    
    # 2. Processamento do payload
    try:
        data = request.json
        logger.info(f"Webhook válido recebido: {data}")
        
        # Implemente sua lógica de negócio aqui
        # Exemplo: atualizar status do pagamento
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return jsonify({"error": "Erro interno"}), 500

@app.route('/check-config', methods=['GET'])
def check_config():
    """Endpoint para verificar configuração"""
    return jsonify({
        "webhook_token_configured": bool(WEBHOOK_TOKEN),
        "access_token_configured": bool(ACCESS_TOKEN)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
