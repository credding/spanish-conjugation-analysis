import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

import curl_cffi
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


@dataclass
class DLEPage:
    word: str
    content: bytes

    @property
    def url(self) -> str:
        return _get_page_url(self.word)

    @property
    def document(self) -> BeautifulSoup:
        return BeautifulSoup(self.content, "html.parser")


class DLEWeb:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir
        self._session = curl_cffi.Session(impersonate="firefox", raise_for_status=True)
        self._pages: dict[str, DLEPage] = {}

        if self._cache_dir is not None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_page(self, word: str) -> DLEPage:
        if word in self._pages:
            return self._pages[word]

        page = self._get_page(word)
        self._pages[word] = page
        if word != page.word:
            self._pages[page.word] = page
        return page

    def _get_page(self, word: str) -> DLEPage:
        if self._cache_dir is None:
            return self._get_page_from_web(word)

        page = _get_page_from_disk(self._cache_dir, word)
        if page is not None:
            return page

        page = self._get_page_from_web(word)
        _save_page_to_disk(self._cache_dir, word, page)
        return page

    def _get_page_from_web(self, word: str) -> DLEPage:
        request_url = _get_page_url(word)
        _logger.info("get DLE page: %s %s", word, request_url)

        response = self._session.get(request_url)
        response_word = unquote(PurePosixPath(urlsplit(response.url).path).parts[-1])

        return DLEPage(response_word, response.content)


def _get_page_url(word: str) -> str:
    return f"https://dle.rae.es/{quote(word)}"


def _get_page_from_disk(cache_dir: Path, word: str) -> DLEPage | None:
    page_path = cache_dir / f"{word}.html"
    if not page_path.is_file():
        return None

    resolved_path = page_path.resolve()
    resolved_word = resolved_path.name.removesuffix(".html")

    return DLEPage(resolved_word, resolved_path.read_bytes())


def _save_page_to_disk(cache_dir: Path, word: str, page: DLEPage) -> None:
    page_path = cache_dir / f"{page.word}.html"
    page_path.write_bytes(page.content)

    if word != page.word:
        link_path = cache_dir / f"{word}.html"
        link_path.symlink_to(page_path.relative_to(cache_dir))
