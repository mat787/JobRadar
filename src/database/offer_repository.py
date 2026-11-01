from dataclasses import fields

from psycopg.rows import dict_row

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
    updates.append("is_active = true")
    updates.append("deactivated_at = NULL")

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

    def offers_without_details(self, limit, exclude_ids=()):
        """Zwraca oferty z bazy (jako JobOffer), dla których nie pobrano jeszcze szczegółów."""
        with self.db.conn.cursor(row_factory=dict_row) as cur:
            rows = cur.execute(
                f"""
                SELECT {', '.join(COLUMNS)} FROM offers
                WHERE details_fetched_at IS NULL
                  AND url IS NOT NULL
                  AND NOT (id = ANY(%s))
                ORDER BY first_seen
                LIMIT %s
                """,
                (list(exclude_ids), limit),
            ).fetchall()
        return [JobOffer(**{column: row[column] for column in COLUMNS}) for row in rows]

    def save_details(self, offers):
        """Zapisuje tylko kolumny ze szczegółów oferty."""
        assignments = ", ".join(f"{column} = %({column})s" for column in DETAIL_FIELDS)
        with self.db.conn.cursor() as cur:
            cur.executemany(
                f"UPDATE offers SET {assignments} WHERE id = %(id)s",
                [vars(offer) for offer in offers],
            )

    def save(self, offers):
        """Dodaje nowe oferty, a istniejące aktualizuje (i odświeża last_seen)."""
        with self.db.conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, [vars(offer) for offer in offers])

    def known_ids(self, ids):
        """Zwraca te id z podanych, które już są w bazie."""
        rows = self.db.conn.execute("SELECT id FROM offers WHERE id = ANY(%s)", (list(ids),)).fetchall()
        return {row[0] for row in rows}

    def deactivate_expired(self):
        """Oznacza jako nieaktywne oferty, którym minęła data ważności."""
        return self.db.conn.execute(
            "UPDATE offers SET is_active = false, deactivated_at = now() "
            "WHERE is_active AND expires_at < now()"
        ).rowcount

    def deactivate_unseen(self, since):
        """Oznacza jako nieaktywne oferty, których nie było na liście od podanego momentu."""
        return self.db.conn.execute(
            "UPDATE offers SET is_active = false, deactivated_at = now() "
            "WHERE is_active AND last_seen < %s",
            (since,),
        ).rowcount

    def count(self, active_only=False):
        sql = "SELECT count(*) FROM offers" + (" WHERE is_active" if active_only else "")
        return self.db.conn.execute(sql).fetchone()[0]
