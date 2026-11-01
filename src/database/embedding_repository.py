from psycopg.rows import dict_row


class EmbeddingRepository:
    """Zapytania SQL dotyczące tabeli offer_embeddings."""

    def __init__(self, db):
        self.db = db

    def offers_without_embedding(self, limit, model, text_version):
        """Oferty ze szczegółami bez wektora albo z wektorem z innego modelu / starszego przepisu na tekst."""
        with self.db.conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(
                """
                SELECT o.id, o.title, o.technologies, o.technologies_optional, o.requirements,
                       o.nice_to_have, o.responsibilities, o.about_project
                FROM offers o
                LEFT JOIN offer_embeddings e ON e.offer_id = o.id
                WHERE o.details_fetched_at IS NOT NULL
                  AND (e.offer_id IS NULL OR e.model <> %s OR e.text_version < %s)
                ORDER BY o.id
                LIMIT %s
                """,
                (model, text_version, limit),
            ).fetchall()

    def save(self, offer_ids, vectors, model, text_version):
        """Zapisuje wektory ofert; istniejące nadpisuje."""
        with self.db.conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO offer_embeddings (offer_id, embedding, model, text_version)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (offer_id) DO UPDATE SET
                    embedding    = EXCLUDED.embedding,
                    model        = EXCLUDED.model,
                    text_version = EXCLUDED.text_version,
                    created_at   = now()
                """,
                [(offer_id, vector, model, text_version) for offer_id, vector in zip(offer_ids, vectors)],
            )

    def count(self):
        return self.db.conn.execute("SELECT count(*) FROM offer_embeddings").fetchone()[0]
