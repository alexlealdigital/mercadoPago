import mercadopago
import os
from dotenv import load_dotenv

load_dotenv()

def gerar_link_pagamento(titulo, preco, nome, email):
    sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

    payment_data = {
        "items": [
            {
                "id": "1",
                "title": titulo,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": preco
            }
        ],
        "back_urls": {
            "success": os.getenv("URL_SUCESSO"),
            "failure": os.getenv("URL_ERRO"),
            "pending": os.getenv("URL_ERRO"),
        },
        "auto_return": "all",
        "metadata": {
            "nome": nome,
            "email": email
        }
    }

    result = sdk.preference().create(payment_data)
    payment = result["response"]
    link_iniciar_pagamento = payment["init_point"]
    return link_iniciar_pagamento
