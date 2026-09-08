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
- `docs/adding-a-library.md` — how to add a new library
- `docs/future-directions.md` — tentative proposals (keyword field, REPL,
  notebook-style agent harnesses) with their tradeoffs
- `docs/personas.md` — Noah (NOOA agent), Hank (shell-only agent), Broman
  (human): who consumes what, and the feature × persona matrix
- `docs/test_plan.md` — how to test the almanack with real agents and users
  (8 tasks, scoring grid, known hazards)
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
uv run poor-richard --ask "molar mass of water"
                                    # fuzzy-lookup: '<score> <card id>' per line
uv run pytest                       # run all golden questions offline
```

`--ask` ranks the cards against the query (token coverage of question text,
provenance and notes, plus a fuzzy name match so `color` finds
`colour-science`) and prints one `<score> <card id>` line per match — a
script-friendly pointer, not the answer itself. Follow up with
`--example <id>` or `poor_richard.search("...")` (which also returns the
matched question and its verified answer) for the details.

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
