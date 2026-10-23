import os

import psycopg
from dotenv import load_dotenv


class Database:
    """Połączenie z bazą Postgres, używane jako context manager (with Database() as db)."""

    def __init__(self):
        load_dotenv()
        self.host = os.environ["DB_HOST"]
        self.port = os.environ["DB_PORT"]
        self.user = os.environ["DB_USER"]
        self.password = os.environ["DB_PASSWORD"]
        self.dbname = os.environ["DB_NAME"]
        self.conn = None

    def __enter__(self):
        self.conn = psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.dbname,
            connect_timeout=10,
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
