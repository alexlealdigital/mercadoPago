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

if __name__ == "__main__":
    app.run(debug=True)
