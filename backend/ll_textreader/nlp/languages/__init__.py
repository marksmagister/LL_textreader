"""Language adapters, found by module name.

A language is added by dropping `<code>.py` in here exposing `adapter()`. Nothing
else in the codebase should need to learn that it exists.
"""

import importlib
from typing import Protocol

from ...models import AnalysedToken


class Adapter(Protocol):
    lang: str

    @property
    def pipeline_id(self) -> str:
        """e.g. "spacy/fr_core_news_md@3.8.0" — stamped onto every token stream."""

    def analyse(self, text: str) -> list[AnalysedToken]: ...


class UnknownLanguage(Exception):
    pass


_cache: dict[str, Adapter] = {}


def get_adapter(lang: str) -> Adapter:
    """Load (once) the adapter for `lang`. Models are heavy; this caches them."""
    if lang not in _cache:
        try:
            module = importlib.import_module(f"{__name__}.{lang}")
        except ModuleNotFoundError as exc:
            raise UnknownLanguage(lang) from exc
        _cache[lang] = module.adapter()
    return _cache[lang]
