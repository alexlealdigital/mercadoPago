# db.py atualizado
import os
from psycopg2 import pool

# Configuração via variáveis de ambiente
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

def salvar_pagamento(pagamento_id, nome, email, titulo, valor, status):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pagamentos 
                (id, nome, email, titulo, valor, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pagamento_id, nome, email, titulo, valor, status))
            conn.commit()
    finally:
        connection_pool.putconn(conn)
