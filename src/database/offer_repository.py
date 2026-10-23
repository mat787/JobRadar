from dataclasses import fields

from scraper.jobOffer import DETAIL_FIELDS, JobOffer

COLUMNS = [f.name for f in fields(JobOffer)]


def build_upsert_sql():
    updates = []
    for column in COLUMNS:
        if column == 'id':
            continue
        if column in DETAIL_FIELDS:
            updates.append(
                f"{column} = CASE WHEN EXCLUDED.details_fetched_at IS NULL "
                f"THEN offers.{column} ELSE EXCLUDED.{column} END"
            )
        else:
            updates.append(f"{column} = EXCLUDED.{column}")
    updates.append("last_seen = now()")

    return (
        f"INSERT INTO offers ({', '.join(COLUMNS)}) "
        f"VALUES ({', '.join(f'%({c})s' for c in COLUMNS)}) "
        f"ON CONFLICT (id) DO UPDATE SET {', '.join(updates)}"
    )


UPSERT_SQL = build_upsert_sql()


class OfferRepository:
    """Zapytania SQL dotyczące tabeli offers."""

    def __init__(self, db):
        self.db = db

    def ids_with_details(self, ids):
        """Zwraca te id z podanych, dla których szczegóły oferty są już w bazie."""
        rows = self.db.conn.execute(
            "SELECT id FROM offers WHERE id = ANY(%s) AND details_fetched_at IS NOT NULL",
            (list(ids),),
        ).fetchall()
        return {row[0] for row in rows}

    def save(self, offers):
        """Dodaje nowe oferty, a istniejące aktualizuje (i odświeża last_seen)."""
        with self.db.conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, [vars(offer) for offer in offers])

    def count(self):
        return self.db.conn.execute("SELECT count(*) FROM offers").fetchone()[0]
