from __future__ import annotations

import app.core.Validator as validator_mod
from app.core.SensitiveWordFilter import SensitiveWordFilter
from app.core.Validator import Validator


def test_nickname_sensitive_word_blocked_in_chinese() -> None:
    ok, reason = Validator.validate_nickname("毒品道友")
    assert ok is False
    assert reason == "昵称包含敏感词汇"


def test_sensitive_filter_english_detected_by_local_en_lexicon() -> None:
    filter_instance = SensitiveWordFilter(words=["毒品", "赌博", "shit"])
    assert filter_instance.check("you are shit") is True


def test_nickname_without_sensitive_word_passes() -> None:
    ok, reason = Validator.validate_nickname("青松明月")
    assert ok is True
    assert reason == "昵称合法"


def test_nickname_sensitive_checker_error_falls_back_to_pass(monkeypatch) -> None:
    def _raise_error():
        raise RuntimeError("sensitive filter unavailable")

    monkeypatch.setattr(validator_mod, "get_sensitive_word_filter", _raise_error)

    ok, reason = Validator.validate_nickname("青松明月")
    assert ok is True
    assert reason == "昵称合法"
