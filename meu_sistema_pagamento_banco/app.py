import logging
logging.basicConfig(level=logging.DEBUG)
from flask import Flask, render_template, request, redirect, jsonify
from apimercadopago import gerar_link_pagamento
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

if __name__ == "__main__":
    app.run(debug=True)
