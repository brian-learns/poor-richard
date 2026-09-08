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
- `tests/test_golden.py` — the golden questions; every test runs with the
  network blocked (`tests/conftest.py`)
- `tests/test_registry.py` — registry integrity (imports, question↔test linkage,
  sync with `pyproject.toml`)

## Usage

```sh
uv sync
uv run poor-richard          # print the reference-card registry
uv run pytest tests/         # run all golden questions offline
```

```python
from poor_richard import CARDS, get

card = get("pycountry")
card.provenance      # "ISO 3166-1/2/3, 639-3, 4217, 15924 ..."
card.questions       # golden questions + known-correct answers
```
