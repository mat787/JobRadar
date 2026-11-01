from database.connection import Database
from database.embedding_repository import EmbeddingRepository
from llm.embedder import Embedder
from rag.documents import TEXT_VERSION, build_offer_text

BATCH_SIZE = 32


def index_offers():
    """Liczy wektory dla ofert bez wektora lub z wektorem z innego modelu / starszego przepisu na tekst."""
    embedder = Embedder(batch_size=BATCH_SIZE)

    with Database() as db:
        repo = EmbeddingRepository(db)
        done = 0

        while True:
            rows = repo.offers_without_embedding(BATCH_SIZE, embedder.model, TEXT_VERSION)
            if not rows:
                break

            texts = [build_offer_text(row) for row in rows]
            vectors = embedder.embed(texts)
            repo.save([row['id'] for row in rows], vectors, embedder.model, TEXT_VERSION)
            db.conn.commit()

            done += len(rows)
            print(f"Zapisano {done} wektorów (łącznie w bazie: {repo.count()})")

        print(f"Gotowe. Nowych wektorów: {done}")
        return done


if __name__ == '__main__':
    index_offers()
