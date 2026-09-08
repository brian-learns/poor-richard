# Poor Richard

A modern Almanack of reference information in the form of a curated list of
python libraries.

The almanack gives an LLM agent authoritative **offline** answers to factual
questions — ISO codes, physical constants, unit conversions, holiday and
business-day calendars, celestial ephemerides, identifier validation — instead of
hallucinated or web-fetched ones.

## Layout

- `reference-libraries.md` — the curated narrative, grouped by domain
- `docs/reference-cards.md` — the design: question archetypes, evaluation axes,
  the reference-card schema, the golden-question test method, and gotchas
- `src/poor_richard/registry.py` — the machine-readable reference cards
  (provenance, update model, offline status, footprint, license, golden questions)
- `src/poor_richard/tests/test_golden.py` — the golden questions; every test runs
  with the network blocked (`tests/conftest.py`). Lives inside the package so the
  wheel ships it (it backs `poor-richard --example`).
- `src/poor_richard/tests/test_registry.py` — registry integrity (imports,
  question↔test linkage, sync with `pyproject.toml`, example availability)

## Usage

```sh
uv sync
uv run poor-richard                 # print the reference-card registry
uv run poor-richard --help particle # help() text for one module
uv run poor-richard --example       # usage example for every card
uv run poor-richard --example mido  # just one (curated, else derived from its test)
uv run pytest                       # run all golden questions offline
```

`--example` re-emits a card's golden test as a runnable snippet: the calls are
kept, the assertions become `# golden:` comments so the verified values stay
visible. Cards with an awkward test (fixtures, system libs) carry a hand-written
`example` on their card instead.

```python
from poor_richard import CARDS, get

card = get("pycountry")
card.provenance      # "ISO 3166-1/2/3, 639-3, 4217, 15924 ..."
card.questions       # golden questions + known-correct answers
```
