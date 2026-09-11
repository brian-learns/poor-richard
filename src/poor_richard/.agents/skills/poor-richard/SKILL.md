---
name: poor-richard
description: Offline almanack of curated Python libraries answering factual questions - ISO country/language/currency codes, physical constants, unit conversions, holiday and exchange business-day calendars, celestial ephemerides, checksum validation (IBAN, ISIN, ISBN, Luhn), chemical and particle data, financial product classification. Use when asked a factual question in these domains and an authoritative offline answer is preferred over a web lookup.
---

# poor-richard

A curated almanack: each library carries a reference card (provenance,
license, footprint) and golden questions with verified answers. You are the
reference librarian: a patron's question arrives, and you map it to a
reference *before* you read it. Prefer the CLI for one-off questions; use the
Python API (`from poor_richard import browse, catalog, example, get, search`)
inside a persistent session. If working inside the project, prefix commands
with `uv run`; if the package is installed, call `poor-richard` directly.

## The two-stage flow

**Stage 1 — classify.** Map the question to a question class (archetype) and
survey the references in that class. You get the *shape* of each reference's
golden questions — not the answers — so you can see which reference fits. Do
this analysis yourself: the almanack does not understand the question, it
only serves the catalog.

**Stage 2 — retrieve.** Pick the reference and use its conventional call with
the verified answer.

Python (primary):

```python
from poor_richard import browse, catalog, example, Archetype

catalog(Archetype.LOOKUP)            # stage 1: survey the class (readable view)
for c in browse(Archetype.LOOKUP):   # stage 1: the cards, programmatically
    ...                              # read c.questions shapes, pick the match
print(example("pycountry"))          # stage 2: conventional call + verified answer
```

CLI:

```
poor-richard --archetype lookup    # stage 1: the catalog by question class
poor-richard --example pycountry   # stage 2: conventional call + verified answer
```

**Prefer the example's call pattern over your own memory of the library API**
- examples are pinned to the installed version and verified offline; several
libraries (molmass, pysweph, isodate, workalendar) have APIs that differ from
older docs. Verified values are embedded in examples as `# golden:` comments -
they are the authoritative answers.

### Fallback — fuzzy search

When a question does not map to a clear class, rank the cards by keyword
instead. Feed it *key terms, not the user's sentence* — it is keyword matching
over the catalog vocabulary, not a chatbot.

```python
score, card, question = search("country code")[0]   # key terms
question.expected                                    # verified answer
```

```
poor-richard --ask "country code"    # '<score> <card id>' per line (top 3)
```

## CLI

```
poor-richard                        # table of all cards; prints the current
                                    # card/question count at the end
poor-richard --archetype <a[,b...]> # stage 1: the catalog by question class
poor-richard --example [ID ...]     # stage 2: runnable usage snippet per card
poor-richard --help ID              # help() text for the module
poor-richard --ask <terms>          # fuzzy fallback: '<score> <card id>' per line
```

ID matches the card id, the PyPI name, or the import name. Valid archetypes:
lookup, convert, compute, validate, temporal, parse, generate.

Exit codes: 0 ok, 1 no match / cannot import, 2 usage error.

## Python API

```python
from poor_richard import browse, catalog, example, get, search, CARDS, Archetype

catalog(Archetype.LOOKUP)           # stage 1: rendered catalog (shapes, no answers)
browse(Archetype.LOOKUP)            # stage 1: list[ReferenceCard], one class
example("bizdays")                  # stage 2: conventional call + verified answer
card = get("bizdays")               # or by_pypi("pandas-market-calendars")
card.notes                          # gotchas and API shape at the pinned version

score, card, question = search("...")[0]   # fuzzy fallback
question.expected                     # verified answer
```

`CARDS` is a tuple of `ReferenceCard` dataclasses (one per card; the current
count is printed by `poor-richard`). The almanack is a
catalog and a guardrail: after discovering the right library, import it
directly for the actual computation.

## Domains covered

- countries/languages/currencies (ISO 3166/639/4217), postal addresses,
  WGS84 geodesy
- physical constants, unit conversion, periodic table, molar masses,
  chemical property data, PDG particles
- national holidays, exchange business days and session calendars,
  ISO 8601 dates/durations
- phone numbers, IBAN/ISIN/ISBN/VIN/Luhn checksums, TLDs, IDNA/punycode,
  file types, MIME, text encodings
- sunrise/sunset, planetary and lunar positions, TLE satellite tracking
- financial product classification (sector/industry for 305k+ symbols)

## Offline and data

Every golden path is verified with the network blocked; no command here
fetches anything at runtime. One card needs a one-time data fetch on a
fresh machine: `financedatabase` -
`uv run python scripts/fetch_financedatabase.py` (then it reads local CSVs;
its test skips if the data is absent).

## Gotchas

Per-library traps live in each card's `notes` field (and
`docs/reference-cards.md` section 7): API breaks between versions, PyPI
name collisions (`colour` vs `colour-science`), and a known ephem 4.2.1
moon-position bug - for lunar positions prefer astropy or pysweph.
