"""Integrity checks for the reference-card registry.

Enforce the golden-question method at the metadata level:
- every card is internally well-formed,
- every carded library is actually importable,
- verified questions point at real tests in tests/test_golden.py,
- the registry stays in sync with pyproject.toml.
"""

import importlib
import tomllib
from pathlib import Path

import pytest

import poor_richard
from poor_richard import CARDS, by_pypi, get

REPO_ROOT = Path(__file__).resolve().parent.parent


def _test_module():
    import tests.test_golden as tg

    return tg


def test_card_ids_unique():
    ids = [c.id for c in CARDS]
    assert len(ids) == len(set(ids))


def test_pypi_names_unique():
    names = [c.pypi for c in CARDS]
    assert len(names) == len(set(names))


def test_cards_well_formed():
    for card in CARDS:
        assert card.id, card
        assert card.name, card
        assert card.pypi, card
        assert card.import_name, card
        assert card.provenance, card
        assert card.license, card
        assert card.questions or not card.archetypes, f"{card.id}: no questions"
        for q in card.questions:
            assert q.question, card.id
            assert q.expected, card.id
            assert q.status in ("candidate", "verified"), card.id
            if q.status == "verified":
                assert q.test_id, f"{card.id}: verified question has no test_id"


def test_import_names_resolvable():
    from tests.test_golden import LibpostalMissing, _preload_libpostal

    try:
        _preload_libpostal()
    except LibpostalMissing:
        pytest.skip("system libpostal.so.1 not found")
    for card in CARDS:
        importlib.import_module(card.import_name), card.pypi


def test_verified_questions_have_tests():
    tg = _test_module()
    for card in CARDS:
        for q in card.questions:
            if q.status == "verified" and q.test_id is not None:
                assert hasattr(tg, q.test_id), f"{card.id}: missing test {q.test_id}"
                assert callable(getattr(tg, q.test_id)), f"{card.id}: {q.test_id} not callable"


def test_registry_matches_pyproject():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    deps = {d.split("==")[0].split(">=")[0].split("<=")[0].strip() for d in pyproject["project"]["dependencies"]}
    carded = {c.pypi for c in CARDS}
    missing_cards = deps - carded
    missing_deps = carded - deps
    assert not missing_cards, f"dependencies without a card: {missing_cards}"
    assert not missing_deps, f"cards without a dependency: {missing_deps}"


def test_lookups():
    assert get("pycountry").pypi == "pycountry"
    assert by_pypi("colour-science").import_name == "colour"
    with pytest.raises(KeyError):
        get("nope")
    with pytest.raises(KeyError):
        by_pypi("nope")


def test_console_script_runs(capsys):
    assert poor_richard.main() == 0
    out = capsys.readouterr().out
    assert "pycountry" in out and "reference cards" in out
