import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from apimercadopago import gerar_link_pagamento
logging.basicConfig(level=logging.DEBUG)
from flask import Flask, render_template, request, redirect, jsonify
from db import salvar_pagamento
from email_utils import enviar_email
import os
from dotenv import load_dotenv
import mercadopago

load_dotenv()

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/pagar", methods=["POST"])
def pagar():
    nome = request.form["nome"]
    email = request.form["email"]
    titulo = request.form["titulo"]
    preco = float(request.form["preco"])

    link = gerar_link_pagamento(titulo, preco, nome, email)
    return redirect(link)

@app.route("/compracerta")
def compra_certa():
    return render_template("compracerta.html")

@app.route("/compraerrada")
def compra_errada():
    return render_template("compraerrada.html")

@app.route("/notificacao", methods=["POST"])
def notificacao():
    try:
        data = request.json
        print("Dados recebidos no webhook:", data)

        if "data" in data and "id" in data["data"]:
            pagamento_id = data["data"]["id"]

            # ========= NOVO BLOCO DE DEBUG =========
            if os.getenv("DEBUG_MODE", "False").lower() == "true":
                print("⚠️ MODO DEBUG ATIVADO - Usando dados mockados")
                pagamento = {
                    "status": "approved",
                    "metadata": {"email": "teste@lizardsplay.com", "nome": "Cliente Teste"},
                    "additional_info": {"items": [{"title": "Produto de Teste"}]},
                    "transaction_amount": 99.90,
                    "id": pagamento_id  # Mantém o ID recebido para consistência
                }
            else:
                # Código original de produção
                sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
                pagamento = sdk.payment().get(pagamento_id)["response"]
            # ========= FIM DO BLOCO DE DEBUG =========

            print("Pagamento recebido do Mercado Pago:", pagamento)

            if pagamento["status"] == "approved":
                email = pagamento.get("metadata", {}).get("email", "cliente@desconhecido.com")
                nome = pagamento.get("metadata", {}).get("nome", "Cliente")                
                print(f">>> E-mail do cliente: {email}")
                
                titulo = pagamento["additional_info"]["items"][0]["title"]
                valor = pagamento["transaction_amount"]

                salvar_pagamento(pagamento_id, nome, email, titulo, valor, "approved")

                corpo_email = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #2e6c80;">Olá, {nome}!</h2>
                    <p>Recebemos seu pagamento com sucesso! 🎉</p>
                    <p><strong>Produto:</strong> {titulo}<br>
                    <strong>Valor:</strong> R$ {valor:.2f}</p>
                    <p>Sua chave de acesso: <strong>MP-{pagamento_id}</strong></p>
                    <p>🦎 <a href="https://www.lizardsplay.com" target="_blank">www.lizardsplay.com</a></p>
                    <hr>
                    <small>Este é um e-mail automático, por favor não responda.</small>
                </body>
                </html>
                """

                enviar_email(email, "✅ Pagamento confirmado!", corpo_email)
                print("📨 E-mail de confirmação enviado")

        return jsonify({"status": "recebido"}), 200

    except Exception as e:
        print("🔥 ERRO NO WEBHOOK:", str(e))
        return jsonify({"status": "erro", "message": str(e)}), 500
        import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from apimercadopago import gerar_link_pagamento
logging.basicConfig(level=logging.DEBUG)
from flask import Flask, render_template, request, redirect, jsonify
from db import salvar_pagamento
from email_utils import enviar_email
import os
from dotenv import load_dotenv
import mercadopago

load_dotenv()

app = Flask(__name__)

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/pagar", methods=["POST"])
def pagar():
    nome = request.form["nome"]
    email = request.form["email"]
    titulo = request.form["titulo"]
    preco = float(request.form["preco"])

    link = gerar_link_pagamento(titulo, preco, nome, email)
    return redirect(link)

@app.route("/compracerta")
def compra_certa():
    return render_template("compracerta.html")

@app.route("/compraerrada")
def compra_errada():
    return render_template("compraerrada.html")

@app.route("/notificacao", methods=["POST"])
def notificacao():
    try:
        print("\n=== DADOS RECEBIDOS ===")
        print(request.data)  # Mostra o JSON bruto
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Modo Debug - Dados mockados completos
        if os.getenv("DEBUG_MODE") == "True":
            print("⚠️ MODO DEBUG ATIVADO - Gerando resposta mockada")
            pagamento = {
                "status": "approved",
                "id": data.get("data", {}).get("id", "DEBUG_123"),
                "metadata": {
                    "email": "teste@lizardsplay.com", 
                    "nome": "Cliente Teste"
                },
                "additional_info": {
                    "items": [{
                        "title": "Produto Teste",
                        "unit_price": 100.50
                    }]
                },
                "transaction_amount": 100.50
            }
        else:
            sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
            pagamento = sdk.payment().get(data["data"]["id"])["response"]

        print("Dados do pagamento:", pagamento)

        if pagamento.get("status") == "approved":
            email = pagamento.get("metadata", {}).get("email")
            nome = pagamento.get("metadata", {}).get("nome")
            print(f"Enviando e-mail para: {email}")
            
            # Seu código de envio de e-mail aqui...
            return jsonify({"status": "sucesso"}), 200

        return jsonify({"status": "pendente"}), 200

    except Exception as e:
        print(f"ERRO: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug")
def debug():
    print("Variáveis de ambiente:", dict(os.environ))
    return "Check no terminal!"

if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    app.run(debug=True)
