import logging
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urlsplit

import curl_cffi
from bs4 import BeautifulSoup

from resources import obj_path

_logger = logging.getLogger(__name__)

_dle_pages_dir = obj_path / "dle_pages"


@dataclass
class DLEPage:
    word: str
    content: bytes

    @property
    def document(self) -> BeautifulSoup:
        return BeautifulSoup(self.content, "html.parser")


class DLEWeb:
    def __init__(self):
        _dle_pages_dir.mkdir(parents=True, exist_ok=True)

        self._session = curl_cffi.Session(impersonate="firefox", raise_for_status=True)
        self._pages: dict[str, DLEPage] = {}

    def get_page(self, word: str) -> DLEPage:
        if word in self._pages:
            return self._pages[word]

        page = self._get_page(word)
        self._pages[word] = page
        if word != page.word:
            self._pages[page.word] = page
        return page

    def _get_page(self, word: str) -> DLEPage:
        page = _get_page_from_disk(word)
        if page is not None:
            return page

        page = self._get_page_from_web(word)
        _save_page_to_disk(word, page)
        return page

    def _get_page_from_web(self, word: str) -> DLEPage:
        request_url = f"https://dle.rae.es/{quote(word)}"
        _logger.info(f"get {word} {request_url}")

        response = self._session.get(request_url)
        response_word = unquote(PurePosixPath(urlsplit(response.url).path).parts[-1])

        return DLEPage(response_word, response.content)


def _get_page_from_disk(word: str) -> DLEPage | None:
    page_path = _dle_pages_dir / f"{word}.html"
    if not page_path.is_file():
        return None

    resolved_path = page_path.resolve()
    resolved_word = resolved_path.name.removesuffix(".html")

    return DLEPage(resolved_word, resolved_path.read_bytes())


def _save_page_to_disk(word: str, page: DLEPage) -> None:
    page_path = _dle_pages_dir / f"{page.word}.html"
    page_path.write_bytes(page.content)

    if word != page.word:
        link_path = _dle_pages_dir / f"{word}.html"
        link_path.symlink_to(page_path.relative_to(_dle_pages_dir))
