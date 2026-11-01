from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class AnalysisRepository:
    """Cache analiz dopasowania (tabela offer_analyses)."""

    def __init__(self, db):
        self.db = db

    def get(self, offer_id, cv_hash, prompt_version):
        with self.db.conn.cursor(row_factory=dict_row) as cur:
            return cur.execute(
                """
                SELECT offer_id, model, score, result, flags, duration_ms, prompt_tokens,
                       completion_tokens, created_at
                FROM offer_analyses
                WHERE offer_id = %s AND cv_hash = %s AND prompt_version = %s
                """,
                (offer_id, cv_hash, prompt_version),
            ).fetchone()

    def analysed_ids(self, offer_ids, cv_hash, prompt_version):
        rows = self.db.conn.execute(
            "SELECT offer_id FROM offer_analyses WHERE offer_id = ANY(%s) AND cv_hash = %s AND prompt_version = %s",
            (list(offer_ids), cv_hash, prompt_version),
        ).fetchall()
        return {row[0] for row in rows}

    def scores(self, offer_ids, cv_hash, prompt_version):
        rows = self.db.conn.execute(
            "SELECT offer_id, score FROM offer_analyses WHERE offer_id = ANY(%s) AND cv_hash = %s AND prompt_version = %s",
            (list(offer_ids), cv_hash, prompt_version),
        ).fetchall()
        return dict(rows)

    def save(self, offer_id, cv_hash, prompt_version, analysis):
        self.db.conn.execute(
            """
            INSERT INTO offer_analyses (offer_id, cv_hash, prompt_version, model, score, result, flags,
                                        duration_ms, prompt_tokens, completion_tokens)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (offer_id, cv_hash, prompt_version) DO UPDATE SET
                model = EXCLUDED.model, score = EXCLUDED.score, result = EXCLUDED.result,
                flags = EXCLUDED.flags, duration_ms = EXCLUDED.duration_ms,
                prompt_tokens = EXCLUDED.prompt_tokens, completion_tokens = EXCLUDED.completion_tokens,
                created_at = now()
            """,
            (offer_id, cv_hash, prompt_version, analysis["model"], analysis["score"], Jsonb(analysis["result"]),
             analysis["flags"], analysis["duration_ms"], analysis["prompt_tokens"], analysis["completion_tokens"]),
        )
