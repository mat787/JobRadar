import json
from bs4 import BeautifulSoup


from .httphandler import HttpHandler
from .jobOffer import JobOffer


class PracujScraper:

    def __init__(self, url):
        self.url = url
        self.http_client = HttpHandler(self.url)

    def _fetch_html(self):
        """Pobiera kod HTML i obsługuje błędy HTTP."""
        status, html_text = self.http_client.send_request()
        if status != 200:
            raise ConnectionError(f"Błąd HTTP: {status}")
        return html_text

    def _extract_json_data(self, html_text):
        """Wydobywa surowy słownik JSON z kodu strony."""
        soup = BeautifulSoup(html_text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')

        if not script_tag:
            raise ValueError("Nie znaleziono tagu '__NEXT_DATA__'.")

        return json.loads(script_tag.text)

    def get_offers(self):
        """Główna metoda zwracająca listę obiektów JobOffer."""
        try:
            html_text = self._fetch_html()
            json_data = self._extract_json_data(html_text)

            queries = json_data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
            extracted_offers = []

            for query in queries:
                data_dict = query.get('state', {}).get('data', {})

                if isinstance(data_dict, dict) and 'groupedOffers' in data_dict:
                    raw_offers = data_dict['groupedOffers']

                    for offer_data in raw_offers:
                        sub_offers = offer_data.get('offers', [])
                        first_sub = sub_offers[0] if sub_offers else {}

                        offer_obj = JobOffer(offer_data, first_sub)
                        extracted_offers.append(offer_obj)

                    break

            return extracted_offers

        except Exception as e:
            print(f"Scrapowanie przerwane z powodu błędu: {e}")
            return []