import random
import time

from database.connection import Database
from database.init_db import init_db
from database.offer_repository import OfferRepository
from main import fetch_with_retry
from scraper.scraper import PracujScraper

BATCH_SIZE = 25


def fill_details():
    """Pobiera szczegóły ofert, które są już w bazie, bezpośrednio z ich zapisanych URL-i."""
    scraper = PracujScraper()
    failed_ids = set()
    done = 0
    empty = 0

    with Database() as db:
        init_db(db)
        db.conn.commit()
        repo = OfferRepository(db)

        while True:
            offers = repo.offers_without_details(BATCH_SIZE, failed_ids)
            if not offers:
                break

            fetched = []
            for offer in offers:
                try:
                    sections = fetch_with_retry(scraper.get_offer_details, offer.url)
                except Exception as e:
                    print(f"  Pomijam {offer.url}: {e}")
                    failed_ids.add(offer.id)
                    continue
                offer.apply_details(sections)
                fetched.append(offer)
                if not sections:
                    empty += 1
                time.sleep(random.uniform(1.5, 3.5))

            repo.save_details(fetched)
            db.conn.commit()
            done += len(fetched)
            print(f"Uzupełniono {done} ofert (bez treści: {empty}, błędy: {len(failed_ids)})")

    print(f"Gotowe. Uzupełniono: {done}, bez treści (np. wygasłe): {empty}, błędy: {len(failed_ids)}")


if __name__ == '__main__':
    fill_details()
