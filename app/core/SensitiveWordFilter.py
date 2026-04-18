from __future__ import annotations

from pathlib import Path
from threading import Lock

import ahocorasick

from app.core.Logger import logger


class SensitiveWordFilter:
    """统一敏感词检测器（本地词库 + Aho-Corasick）"""

    def __init__(self, words: list[str]):
        self._words = words
        self._automaton = ahocorasick.Automaton()
        for word in words:
            self._automaton.add_word(word, word)
        self._automaton.make_automaton()

    @staticmethod
    def normalize(text: str) -> str:
        return text.strip().lower()

    def find_matches(self, text: str) -> list[str]:
        normalized = self.normalize(text)
        matches: list[str] = []
        seen: set[str] = set()

        for _, matched in self._automaton.iter(normalized):
            if matched not in seen:
                seen.add(matched)
                matches.append(matched)

        return matches

    def check(self, text: str) -> bool:
        try:
            return len(self.find_matches(text)) > 0
        except Exception:
            logger.exception("[SENSITIVE] check failed, fallback pass")
            return False


_FILTER_INSTANCE: SensitiveWordFilter | None = None
_INIT_LOCK = Lock()


def _default_lexicon_path() -> Path:
    return Path(__file__).resolve().parent.parent / "resources"


def _load_words(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"sensitive lexicon file not found: {path}")

    words: list[str] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if not word or word.startswith("#"):
                continue
            normalized = SensitiveWordFilter.normalize(word)
            if normalized and normalized not in seen:
                seen.add(normalized)
                words.append(normalized)

    if not words:
        raise ValueError(f"sensitive lexicon is empty: {path}")
    return words


def init_sensitive_word_filter() -> SensitiveWordFilter:
    global _FILTER_INSTANCE
    if _FILTER_INSTANCE is not None:
        return _FILTER_INSTANCE

    with _INIT_LOCK:
        if _FILTER_INSTANCE is not None:
            return _FILTER_INSTANCE
        base_dir = _default_lexicon_path()
        zh_path = base_dir / "sensitive_words_zh.txt"
        en_path = base_dir / "sensitive_words_en.txt"
        zh_words = _load_words(zh_path)
        en_words = _load_words(en_path)
        words = sorted(set(zh_words + en_words))
        _FILTER_INSTANCE = SensitiveWordFilter(words=words)
        logger.info(
            "[SENSITIVE] initialized - total_words=%d zh_words=%d en_words=%d zh_path=%s en_path=%s",
            len(words),
            len(zh_words),
            len(en_words),
            str(zh_path),
            str(en_path),
        )
        return _FILTER_INSTANCE


def get_sensitive_word_filter() -> SensitiveWordFilter:
    if _FILTER_INSTANCE is None:
        return init_sensitive_word_filter()
    return _FILTER_INSTANCE
