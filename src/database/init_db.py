from pathlib import Path

from database.connection import Database

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(db):
    """Tworzy tabele ze schema.sql (istniejących nie rusza)."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    db.conn.execute(schema_sql)


if __name__ == "__main__":
    with Database() as db:
        init_db(db)
    print("Baza zainicjalizowana.")
