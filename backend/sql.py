import os
import pymysql
from pymysql import Connection
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection(autocommit: bool = True) -> Connection:
    db_conf = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 4000)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_DATABASE"),
        "autocommit": autocommit,
        "cursorclass": DictCursor,
    }
    
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        db_conf["ssl_verify_cert"] = True
        db_conf["ssl_verify_identity"] = True
        db_conf["ssl_ca"] = ssl_ca

    return pymysql.connect(**db_conf)

def execute_query(query: str, params=None, fetch_one=False, fetch_all=False, batch=False):
    """Execute a query and return results"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if batch: cur.executemany(query, params)
            else: cur.execute(query, params)
            if fetch_one:
                return cur.fetchone()
            elif fetch_all:
                return cur.fetchall()
            return cur.rowcount