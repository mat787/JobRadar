import json
from bs4 import BeautifulSoup


from .httphandler import HttpHandler
from .jobOffer import JobOffer, clean_text


class PracujScraper:

    def __init__(self):
        self.http_client = HttpHandler()

    def _fetch_html(self, url):
        """Pobiera kod HTML i obsługuje błędy HTTP."""
        status, html_text = self.http_client.send_request(url)
        if status != 200:
            raise ConnectionError(f"Błąd HTTP {status}: {url}")
        elif "Nie znaleziono strony" in html_text:
            raise ValueError(f"Nie znaleziono strony: {url}")
        return html_text

    def _extract_queries(self, html_text):
        """Wydobywa listę zapytań z JSON-a '__NEXT_DATA__' w kodzie strony."""
        soup = BeautifulSoup(html_text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')

        if not script_tag:
            raise ValueError("Nie znaleziono tagu '__NEXT_DATA__'.")

        json_data = json.loads(script_tag.text)
        return json_data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])

    def get_offers(self, url):
        """Zwraca listę obiektów JobOffer ze strony z listą ofert (pusta lista = koniec stron)."""
        queries = self._extract_queries(self._fetch_html(url))

        for query in queries:
            data_dict = query.get('state', {}).get('data', {})

            if isinstance(data_dict, dict) and 'groupedOffers' in data_dict:
                return [JobOffer.from_api(offer_data) for offer_data in data_dict['groupedOffers']]

        raise ValueError(f"Brak listy ofert na stronie: {url}")

    def get_offer_details(self, offer_url):
        """Zwraca sekcje oferty jako słownik {sectionType: [punkty]}."""
        queries = self._extract_queries(self._fetch_html(offer_url))

        for query in queries:
            if query.get('queryKey', [None])[0] != 'jobOffer':
                continue

            sections = {}
            for section in query['state']['data'].get('textSections', []):
                items = [clean_text(element) for element in section.get('textElements', [])]
                items = [item for item in items if item]
                if items:
                    sections.setdefault(section.get('sectionType'), []).extend(items)
            return sections

        return {}
