import argparse
import random
import time

from database.connection import Database
from database.init_db import init_db
from database.offer_repository import OfferRepository
from scraper.scraper import PracujScraper

BASE_URL = 'https://it.pracuj.pl/praca?sc=0'
MAX_RETRIES = 3
STOP_AFTER = 2


def page_url(pn):
    return BASE_URL if pn == 1 else f'{BASE_URL}&pn={pn}'


def fetch_with_retry(func, *args):
    """Wywołuje func; przy błędzie czeka coraz dłużej i próbuje ponownie."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args)
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            pause = 30 * attempt
            print(f"  Błąd ({e}). Próba {attempt}/{MAX_RETRIES}, ponawiam za {pause} s...")
            time.sleep(pause)
    return None


def fetch_details(scraper, offers):
    """Uzupełnia szczegóły ofert; błąd pojedynczej oferty nie przerywa całości."""
    for i, offer in enumerate(offers, start=1):
        if not offer.url:
            continue
        try:
            offer.apply_details(fetch_with_retry(scraper.get_offer_details, offer.url))
        except Exception as e:
            print(f"  Pomijam szczegóły oferty {offer.url}: {e}")
        print(f"  Szczegóły {i}/{len(offers)}", end='\r')
        time.sleep(random.uniform(1.5, 3.5))


def main(max_pages, incremental=False):
    """Pobiera listę ofert; w trybie przyrostowym kończy po STOP_AFTER stronach bez nowych ofert.

    Zwraca statystyki przebiegu; 'reached_end' = True, gdy przeszliśmy całą listę (pełny przebieg).
    """
    scraper = PracujScraper()
    stats = {'pages': 0, 'new_offers': 0, 'reached_end': False}
    pages_without_new = 0

    with Database() as db:
        init_db(db)
        db.conn.commit()
        repo = OfferRepository(db)

        for pn in range(1, max_pages + 1):
            offers = fetch_with_retry(scraper.get_offers, page_url(pn))

            if not offers:
                print(f"Brak ofert na stronie {pn}. Kończę pobieranie.")
                stats['reached_end'] = True
                break

            ids = [offer.id for offer in offers]
            new_ids = set(ids) - repo.known_ids(ids)
            with_details = repo.ids_with_details(ids)
            to_fetch = [offer for offer in offers if offer.id not in with_details]
            print(f"Strona {pn}: {len(offers)} ofert, nowych: {len(new_ids)}, do pobrania szczegółów: {len(to_fetch)}")
            fetch_details(scraper, to_fetch)

            repo.save(offers)
            db.conn.commit()
            stats['pages'] = pn
            stats['new_offers'] += len(new_ids)
            print(f"Strona {pn} zapisana. Ofert w bazie: {repo.count()}")

            pages_without_new = 0 if new_ids else pages_without_new + 1
            if incremental and pages_without_new >= STOP_AFTER:
                print(f"{STOP_AFTER} strony z rzędu bez nowych ofert. Kończę tryb przyrostowy.")
                break

            if pn % 10 == 0:
                oddech = random.uniform(15.0, 30.0)
                print(f"Paczka 10 stron pobrana. Chwila oddechu... ({oddech:.1f} s)")
                time.sleep(oddech)
            else:
                time.sleep(random.uniform(2.5, 5.5))

        print(f"Gotowe. Łącznie ofert w bazie: {repo.count()}, nowych w tym przebiegu: {stats['new_offers']}")
    return stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pobiera oferty IT z pracuj.pl do bazy.")
    parser.add_argument('--max-pages', type=int, default=200,
                        help="maksymalna liczba stron listy ofert (domyślnie: wszystkie)")
    parser.add_argument('--incremental', action='store_true',
                        help=f"zakończ po {STOP_AFTER} stronach z rzędu bez nowych ofert")
    args = parser.parse_args()
    main(args.max_pages, incremental=args.incremental)
