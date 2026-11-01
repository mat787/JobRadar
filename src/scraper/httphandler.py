from curl_cffi import requests


class HttpHandler:
    """Wysyła zapytania HTTP, podszywając się pod przeglądarkę Chrome."""

    def __init__(self, timeout=30):
        self.timeout = timeout

    def send_request(self, url):
        r = requests.get(
            url,
            impersonate="chrome120",
            timeout=self.timeout,
            headers={"Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"},
        )
        return r.status_code, r.text
