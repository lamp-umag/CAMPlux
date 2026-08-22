import time
import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "camplux-Quarry/1.0 (academic corpus research, Magallanes media; "
        "contact: culpem@research.local)"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.5",
}

ARTICLE_FIELDS = ["source", "date", "title", "url", "body_text", "section"]


class BaseScraper:
    name = "Base"
    base_url = ""
    min_delay = 1.0   # override per scraper to respect robots.txt
    region  = "magallanes"   # "magallanes" | "nacional" | "regional"
    enabled = True           # False = shown in UI but not scrapeable
    note    = ""             # reason shown when enabled=False

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get(self, url, delay=1.5, retries=2, **kwargs):
        """Fetch URL with retry on network errors. HTTP errors are not retried."""
        self._last_status = 0
        actual_delay = max(delay, self.min_delay)
        time.sleep(actual_delay)
        for attempt in range(1 + retries):
            try:
                r = self.session.get(url, timeout=30, **kwargs)
                r.raise_for_status()
                return r
            except requests.exceptions.HTTPError as e:
                self._last_status = e.response.status_code
                logger.warning("HTTP %s: %s", self._last_status, url)
                return None  # HTTP errors (4xx/5xx) — don't retry
            except requests.RequestException as e:
                if attempt < retries:
                    wait = 3 * (attempt + 1)
                    logger.warning("Attempt %d failed (%s), retrying in %ds…", attempt + 1, e, wait)
                    time.sleep(wait)
                else:
                    logger.warning("Failed after %d attempts: %s — %s", attempt + 1, url, e)
                    return None

    def clean_html(self, html_or_soup):
        """Strip tags and collapse to a single-line string.

        Single-line output keeps CSV cells intact regardless of quote content.
        JSONL consumers can treat whitespace runs as paragraph breaks if needed.
        """
        if isinstance(html_or_soup, str):
            soup = BeautifulSoup(html_or_soup, "lxml")
        else:
            soup = html_or_soup
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "figure", "figcaption", "iframe", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        # Collapse all whitespace (spaces, tabs, newlines) to single space
        return re.sub(r"\s+", " ", text).strip()

    def in_date_range(self, date_str, date_from, date_to):
        if not date_str:
            return True
        d = date_str[:10]
        if date_from and d < date_from[:10]:
            return False
        if date_to and d > date_to[:10]:
            return False
        return True

    def run(self, query="", date_from="", date_to="", delay=1.5):
        raise NotImplementedError
