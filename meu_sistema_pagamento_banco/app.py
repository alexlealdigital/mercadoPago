from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Configurações (substitua com seus dados)
EMAIL_CONFIG = {
    "from": "seu_email@exemplo.com",
    "password": os.getenv("EMAIL_PASSWORD"),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        payment_status = data.get('action')
        payment_data = data.get('data', {})
        
        if payment_status == 'payment.updated' and payment_data.get('status') == 'approved':
            send_download_links(
                email=payment_data.get('payer', {}).get('email'),
                payment_id=payment_data.get('id')
            )
            
        return jsonify({"status": "processed"}), 200
        
    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return jsonify({"error": "internal error"}), 500

def send_download_links(email: str, payment_id: str):
    """Envia e-mail com links de download"""
    if not email:
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
    
    with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
        server.starttls()
        server.login(EMAIL_CONFIG['from'], EMAIL_CONFIG['password'])
        server.send_message(msg)
    print(f"E-mail enviado para {email}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
