import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

def gerar_link_pagamento(titulo, preco, nome, email):
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
    
    # Seleciona URLs conforme ambiente
    if os.getenv("FLASK_ENV") == "development":
        success_url = os.getenv("DEV_URL_SUCESSO")
        failure_url = os.getenv("DEV_URL_ERRO")
    else:
        success_url = os.getenv("PROD_URL_SUCESSO")
        failure_url = os.getenv("PROD_URL_ERRO")

    payment_data = {
        "items": [{
            "title": titulo,
            "quantity": 1,
            "unit_price": float(preco),
            "currency_id": "BRL"
        }],
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": failure_url
        },
        "auto_return": "approved",
        "metadata": {
            "nome": nome,
            "email": email
        }
    }
    
    try:
        preference = sdk.preference().create(payment_data)
        return preference["response"]["init_point"]
    except Exception as e:
        print(f"Erro ao criar preferência: {str(e)}")
        return None
