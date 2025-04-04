import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def salvar_pagamento(pagamento_id, nome, email, titulo, valor, status):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pagamentos (pagamento_id, nome, email, titulo, valor, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (pagamento_id, nome, email, titulo, valor, status)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Pagamento {pagamento_id} salvo com sucesso!")
    except Exception as e:
        print("Erro ao salvar no banco:", e)
