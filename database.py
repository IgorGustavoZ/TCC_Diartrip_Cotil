import mysql.connector
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

def conectar_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@contextmanager
def get_db():
    conexao = conectar_db()
    try:
        yield conexao
    finally:
        conexao.close()