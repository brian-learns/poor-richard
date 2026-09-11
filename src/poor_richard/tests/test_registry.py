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
from poor_richard import CARDS, Archetype, browse, by_pypi, catalog, example, get, search
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


def _optional_packages():
    """pypi names in [project.optional-dependencies] — may be absent in a base install."""
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    groups = pyproject.get("project", {}).get("optional-dependencies", {}).values()
    return {
        d.split(">=")[0].split("<=")[0].strip()
        for group in groups
        for d in group
    }


def test_import_names_resolvable():
    from poor_richard.tests.test_golden import LibpostalMissing, _preload_libpostal

    try:
        _preload_libpostal()
    except LibpostalMissing:
        pytest.skip("system libpostal.so.1 not found")
    optional = _optional_packages()
    for card in CARDS:
        try:
            importlib.import_module(card.import_name)
        except ImportError:
            if card.pypi in optional:
                pytest.skip(f"{card.pypi} not installed (optional 'full' extra)")
            raise


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
    deps |= _optional_packages()
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


def test_search_keywords():
    # issue #2: curated keywords field folded into the search corpus
    assert search("convert temperature celsius fahrenheit", top=1)[0][1].id == "pint"
    assert search("holiday calendar NYSE", top=1)[0][1].id == "bizdays"


def test_search_exact_id_wins():
    res = search("bizdays", top=1)
    assert res and res[0][1].id == "bizdays" and res[0][0] >= 1.0


def test_search_no_match():
    assert search("zzzqqq xkcdplugh") == []
    assert search("the of and") == []  # stopwords only


def test_browse_all():
    assert browse() == list(CARDS)


def test_browse_filters_by_archetype():
    lookups = browse(Archetype.LOOKUP)
    assert lookups and len(lookups) < len(CARDS)
    assert all(Archetype.LOOKUP in c.archetypes for c in lookups)
    assert get("pycountry") in lookups          # a lookup card is present
    assert get("molmass") not in lookups        # a compute-only card is not


def test_catalog_shows_shapes_not_answers():
    text = catalog()
    for c in CARDS:                              # every question shape is shown
        for q in c.questions:
            assert q.question in text
    lines = {ln.strip().lstrip("-").strip() for ln in text.splitlines() if ln.strip()}
    for c in CARDS:                              # no answer is emitted as its own line
        for q in c.questions:
            assert q.expected.strip() not in lines


def test_catalog_scoped_to_one_archetype():
    look = catalog(Archetype.LOOKUP)
    assert look.splitlines()[0] == "lookup"
    headers = [ln for ln in look.splitlines() if not ln.startswith(" ")]
    assert headers == ["lookup"]                 # no other archetype sections


def test_example_derives_when_not_curated():
    # a card with no curated .example still yields a runnable snippet
    pyc = example("pycountry")
    assert pyc.strip() and "import pycountry" in pyc
    assert "golden" in pyc                       # verified values stay visible
    # a curated card returns its hand-written snippet
    assert example("mido").strip()


def test_console_ask(capsys):
    assert poor_richard.main(["--ask", "molar", "mass", "of", "water"]) == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0].endswith("molmass") and lines[0].split()[0] == "1.03"
    assert "18.015" not in out  # ranking only: no answers, no examples
    assert poor_richard.main(["--ask"]) == 2


def test_console_browse(capsys):
    assert poor_richard.main(["--archetype", "lookup"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "lookup"
    assert "pycountry" in out
    assert "18.015" not in out  # stage 1: shapes only, no answers
    # multiple archetypes, comma-separated
    assert poor_richard.main(["--archetype", "lookup,convert"]) == 0
    out = capsys.readouterr().out
    headers = [ln for ln in out.splitlines() if not ln.startswith(" ")]
    assert "lookup" in headers and "convert" in headers
    # usage errors
    assert poor_richard.main(["--archetype"]) == 2
    assert poor_richard.main(["--archetype", "bogus"]) == 2


def test_console_script_runs(capsys):
    assert poor_richard.main() == 0
    out = capsys.readouterr().out
    assert "pycountry" in out and "reference cards" in out
