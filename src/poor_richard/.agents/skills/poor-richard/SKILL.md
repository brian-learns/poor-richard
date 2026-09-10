---
name: poor-richard
description: Offline almanack of curated Python libraries answering factual questions - ISO country/language/currency codes, physical constants, unit conversions, holiday and exchange business-day calendars, celestial ephemerides, checksum validation (IBAN, ISIN, ISBN, Luhn), chemical and particle data, financial product classification. Use when asked a factual question in these domains and an authoritative offline answer is preferred over a web lookup.
---

# poor-richard

A curated almanack: each library carries a reference card (provenance,
license, footprint) and golden questions with verified answers. Prefer the
CLI for one-off questions; use the Python API (`from poor_richard import
search, get`) inside a persistent session. If working inside the project,
prefix commands with `uv run`; if the package is installed, call
`poor-richard` directly.

## CLI

```
poor-richard                        # table of all cards; prints the current
                                    # card/question count at the end
poor-richard --ask "QUERY"          # '<score> <card id>' per line (top 3)
poor-richard --example [ID ...]     # runnable usage snippet per card
poor-richard --help ID              # help() text for the module
```

ID matches the card id, the PyPI name, or the import name.

Canonical flow: `--ask "<question>"` to find the card, then
`--example <id>` for the conventional call pattern. **Prefer the example's
call pattern over your own memory of the library API** - examples are
pinned to the installed version and verified offline; several libraries
(molmass, pysweph, isodate, workalendar) have APIs that differ from older
docs. Verified values are embedded in examples as `# golden:` comments -
they are the authoritative answers.

Exit codes: 0 ok, 1 no match / cannot import, 2 usage error.

## Python API

```python
from poor_richard import search, get, CARDS

score, card, question = search("molar mass of water")[0]
question.expected        # verified answer string
card.notes               # gotchas and API shape at the pinned version
card.example             # canonical snippet (curated or derived)

card = get("bizdays")    # or by_pypi("pandas-market-calendars")
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
