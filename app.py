from flask import Flask, request, jsonify
import hmac
import hashlib
import os

app = Flask(__name__)

# 1. Configure ESTAS variáveis no Render.com (Environment Variables)
WEBHOOK_TOKEN = os.getenv('MP_WEBHOOK_TOKEN')  # Token específico de Webhooks (começa com "WH-")
ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN')     # Seu Access Token normal

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 2. Validação SIMPLES e direta da assinatura
        signature = request.headers.get('X-Signature')
        if not signature:
            return jsonify({"error": "Assinatura ausente"}), 401
        
        # 3. Extrai a parte v1 da assinatura (formato "ts=...,v1=...")
        received_hash = signature.split(',')[1].split('=')[1]  # Pega apenas o "v1=hash"
        
        # 4. Gera o hash esperado
        expected_hash = hmac.new(
            WEBHOOK_TOKEN.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        # 5. Comparação SEGURA
        if not hmac.compare_digest(received_hash, expected_hash):
            return jsonify({"error": "Assinatura inválida"}), 401
        
        # 6. Se chegou aqui, está validado!
        data = request.json
        print("✅ Webhook válido recebido:", data)
        
        # Implemente sua lógica aqui (ex: atualizar banco de dados)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print("❌ Erro:", e)
        return jsonify({"error": "Erro interno"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
