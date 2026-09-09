"""Integrity checks for the reference-card registry.

Enforce the golden-question method at the metadata level:
- every card is internally well-formed,
- every carded library is actually importable,
- verified questions point at real tests in poor_richard/tests/test_golden.py,
- the registry stays in sync with pyproject.toml,
- every card has an example source for `poor-richard --example`.
"""

import ast
import importlib
import tomllib
from pathlib import Path

import pytest

import poor_richard
from poor_richard import CARDS, by_pypi, get, search
from poor_richard import _derive_example

REPO_ROOT = Path(__file__).resolve().parents[3]


def _test_module():
    import poor_richard.tests.test_golden as tg

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
    from poor_richard.tests.test_golden import LibpostalMissing, _preload_libpostal

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


def test_verified_answers_pinned_in_golden_tests():
    """Every verified question is pinned in its golden test via ``_expected``.

    Golden tests pin the registry's ``expected`` answer strings to the
    literals they prove, so a data edit in registry.py that drifts from the
    standard fails the suite; this check keeps the pin mandatory.
    """
    tree = ast.parse(Path(__file__).with_name("test_golden.py").read_text())
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for card in CARDS:
        for q in card.questions:
            if q.status != "verified":
                continue
            fn = funcs.get(q.test_id)
            assert fn is not None, f"{card.id}: no test function {q.test_id}"
            literals = {
                n.value
                for n in ast.walk(fn)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            }
            assert q.question in literals, (
                f"{card.id}: {q.question!r} not pinned in {q.test_id}; "
                f"add an _expected() assert"
            )


def test_registry_matches_pyproject():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    deps = {d.split("==")[0].split(">=")[0].split("<=")[0].strip() for d in pyproject["project"]["dependencies"]}
    carded = {c.pypi for c in CARDS}
    missing_cards = deps - carded
    missing_deps = carded - deps
    assert not missing_cards, f"dependencies without a card: {missing_cards}"
    assert not missing_deps, f"cards without a dependency: {missing_deps}"


def test_every_card_has_example_source():
    """`--example` needs a curated snippet or a derivable golden test per card."""
    for card in CARDS:
        if card.example:
            continue
        test_id = next(
            (q.test_id for q in card.questions if q.status == "verified" and q.test_id),
            f"test_{card.id}",
        )
        assert _derive_example(test_id), f"{card.id}: no curated example, no derivable test"


def test_curated_examples_compile():
    for card in CARDS:
        if card.example:
            ast.parse(card.example), f"{card.id}: curated example is not valid python"


def test_lookups():
    assert get("pycountry").pypi == "pycountry"
    assert by_pypi("colour-science").import_name == "colour"
    with pytest.raises(KeyError):
        get("nope")
    with pytest.raises(KeyError):
        by_pypi("nope")


def test_search_question_match():
    res = search("molar mass of water", top=1)
    assert res and res[0][1].id == "molmass"
    assert res[0][2] is not None and "H2O" in res[0][2].question


def test_search_name_typo():
    res = search("color", top=1)
    assert res and res[0][1].id == "colour-science"


def test_search_topics():
    assert search("validate a phone number")[0][1].id == "phonenumbers"
    assert search("IBAN validation")[0][1].id == "python-stdnum"
    assert search("business days NYSE")[0][1].id == "bizdays"


def test_search_exact_id_wins():
    res = search("bizdays", top=1)
    assert res and res[0][1].id == "bizdays" and res[0][0] >= 1.0


def test_search_no_match():
    assert search("zzzqqq xkcdplugh") == []
    assert search("the of and") == []  # stopwords only


def test_console_ask(capsys):
    assert poor_richard.main(["--ask", "molar", "mass", "of", "water"]) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0].endswith("molmass") and lines[0].split()[0] == "1.03"
    assert "18.015" not in out  # ranking only: no answers, no examples
    assert poor_richard.main(["--ask"]) == 2


def test_console_script_runs(capsys):
    assert poor_richard.main() == 0
    out = capsys.readouterr().out
    assert "pycountry" in out and "reference cards" in out
