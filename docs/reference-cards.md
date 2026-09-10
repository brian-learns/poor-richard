# Poor Richard — Reference Card Design

Poor Richard is a modern almanack: a curated set of Python libraries that give an
LLM agent **authoritative offline answers** to factual questions — codes, constants,
conversions, ephemerides, validations — that the model would otherwise hallucinate
or have to resolve via the web.

This document defines:

1. the **question archetypes** a reference library must answer,
2. the **evaluation axes** used to judge the information each library provides,
3. the **reference card schema** (machine-readable, in `poor_richard/registry.py`),
4. the **golden-question test method** that proves a library works offline and is correct,
5. the current **card table**,
6. **candidates** not yet installed and **gotchas** learned while verifying.

The curated narrative lives in `reference-libraries.md`. The machine-readable
cards live in `src/poor_richard/registry.py` (source of truth for card data);
the golden questions live in `tests/test_golden.py`; integrity is enforced by
`tests/test_registry.py`.

---

## 1. Question archetypes

Every library answers one or more of these. Tagging a card with its archetypes is
what makes "what questions can this help answer?" concrete and testable.

| Archetype | Question shape | Example |
|---|---|---|
| **lookup** | "What is X's code / name / value?" | "ISO 3166-1 alpha-3 for France?" → `FRA` |
| **convert** | "Translate X to Y" | "1 kWh in joules?" → `3.6e6 J` |
| **compute** | "Derive Z from inputs" | "Moon phase on 2025-06-15?" |
| **validate** | "Is X well-formed / correct?" | "Does this credit card pass Luhn?" |
| **temporal** | "When does X occur (next / prev / in range)?" | "Next US business day after 2025-12-25?" |
| **parse** | "Break this raw string into structured fields" | "1600 Pennsylvania Ave → {street, city, …}" |
| **generate** | "Emit X in standard form Y" | "Satellite track → CZML packet" |

## 2. Evaluation axes

Each card is scored on:

| Axis | What it asks | How it's checked |
|---|---|---|
| **Provenance** | Which standard/authority is the data derived from (ISO, IANA, NIST, NASA JPL, IUPAC, CIE, …)? Official source or derivative? | Read the project docs / data files; record the standard. |
| **Update model** | Static (physics constants), per-release snapshot (ISO lists, PSL), or algorithmic (no data at all)? | Check release notes; note the newest data vintage if findable. |
| **Offline integrity** | Does it genuinely work with no network — is data **bundled**, or fetched on first use? | Golden test run with sockets blocked (method below). Never assume. |
| **Coverage** | What fraction of the domain? | Spot-check edge cases (e.g. subdivisions, non-ISO languages). |
| **Precision** | For computed values, what accuracy, and are uncertainties stated? | Compare against the standard's stated values. |
| **LLM output shape** | Does the API return clean `dict` / structured objects (easy for a model to consume) or human-oriented strings? | Read the API; prefer structured. |
| **Footprint** | Installed size, native/C deps, wheel availability on the target Python. | `du -sh site-packages/<pkg>`; check for C extensions. |
| **License / maintenance** | Permissive? Actively released? Deterministic across versions? | PyPI metadata; release cadence. |

## 3. Reference card schema

`poor_richard.registry.ReferenceCard` (dataclass):

| Field | Meaning |
|---|---|
| `id` | stable slug (e.g. `"colour-science"`) |
| `name`, `pypi`, `import_name` | human name / PyPI distribution / top-level module |
| `archetypes` | tuple of `Archetype` |
| `provenance` | standard or data source |
| `update_model` | `static` / `per-release snapshot` / `algorithmic` |
| `offline` | works with no network |
| `offline_verified` | golden tests passed with sockets blocked |
| `footprint`, `native_deps`, `license` | as in the evaluation axes |
| `questions` | tuple of `Question(question, expected, status, test_id)` |
| `notes` | API gotchas, version quirks, known bugs |

A question's `status` is `"candidate"` (awaiting a test) or `"verified"` (has a
passing test, whose name is the `test_id`). `tests/test_registry.py` enforces:
unique ids, well-formed cards, importable `import_name`s, verified questions
pointing at real tests, and 1:1 sync between cards and `pyproject.toml` deps.

## 4. Golden-question test method

**Protocol.** For each library, 1–5 golden questions spanning its archetypes. Each
question is a triple:

1. a natural-language question (what an agent might actually ask),
2. an API call that answers it,
3. an **independently known-correct** expected value (from the standard itself —
   e.g. the IBAN spec's example, CODATA, the IANA tz database — not from the
   library's own docs), with a tight tolerance for floats.

**Answer pinning.** Each golden test also pins the registry's `expected`
strings: one `_expected(card, question)` assert per verified question, in the
same test, so an edit to `registry.py` data that drifts from the proven value
fails the suite. `test_registry.py` enforces that every verified question is
pinned.

**Offline enforcement.** `src/poor_richard/tests/conftest.py` installs an autouse
fixture that patches `socket.connect`, `socket.socket.connect_ex`, and
`socket.getaddrinfo` to raise for **every test**, so `uv run pytest` runs fully
offline. Where permitted, `unshare -n uv run pytest` is stronger (kernel-level).

Caveats: the socket patch catches TCP/DNS attempts made *after* interpreter start;
a library that fetches data **at import time** fails loudly (desired). A PASS
means the specific golden path is offline and correct.

**Adding a check for a new library**

1. `uv add <pkg>`.
2. Pick 1–5 questions spanning the library's archetypes; get expected values from
   the standard, not the package docs.
3. Add a `test_<card_id>()` function to `src/poor_richard/tests/test_golden.py`
   (imports inside the function so import-time network fetches are caught),
   with an `_expected()` pin assert per question.
4. Add/extend the card in `poor_richard/registry.py` with the questions,
   `status="verified"`, `test_id="test_<card_id>"`.
5. Run `uv run pytest`; on failure, fix the *test's* API usage or expected value —
   investigate before weakening an assertion.
6. Update the card table in this doc.

**Tests double as usage examples.** `poor-richard --example [id ...]` re-emits a
card's golden test as a runnable snippet: calls kept, assertions turned into
`# golden:` comments. It parses the test source (never imports the libraries),
which is why the tests live inside the package and ship in the wheel. Tests that
use fixtures or system libraries (mido, starfile, postal, networkx) carry a
hand-written `example` field on the card instead; the integrity tests enforce
that every card has one or the other.

**Agent-facing lookup.** `poor-richard --ask "<query>"` (or
`poor_richard.search(query)`) is the fuzzy front door: it ranks cards by
query-token coverage of question text, provenance, notes, and a small curated
`keywords` field (standard-specific terms the docs never use, e.g. `celsius`
for pint; issue #2), plus a `difflib` name-similarity bonus (typos like
`color` → `colour-science`).
The CLI prints one `<score> <card id>` line per match — a pointer, not an
answer; `search()` additionally returns the matched question and its
verified answer for programmatic use. Stdlib only, fully offline; a small
stoplist and naive plural folding (`numbers` → `number`) handle the
paraphrase gap. Card text is therefore curated for discoverability — if a
natural query misses, fix the card's provenance/notes/keywords before adding
machinery (raw `help()`/pydoc text was measured and rejected in issue #2:
it buries the right cards and churns on every library upgrade).

**Status (2026-09):** all 45 cards have passing offline golden examples; 56
verified questions; the ephem moon-phase question is an xfail canary (see §7).

## 5. Card table

Source of truth: `poor_richard.registry.CARDS` (45 entries incl. the auxiliary).
`uv run poor-richard` prints it.

| id | pypi | archetypes | offline | footprint | license |
|---|---|---|---|---|---|
| pycountry | pycountry | lookup | ⚙ verified | 23 MB | LGPL-2.1 |
| python-iso639 | python-iso639 | lookup, convert | ⚙ verified | 432 KB | Apache-2.0 |
| countryinfo | countryinfo | lookup | ⚙ verified | 2 MB | MIT |
| timezonefinder | timezonefinder | convert | ⚙ verified | 372 KB + 63 MB data | MIT |
| postal | pypostal-multiarch | parse, convert | ⚙ verified | 916 KB + system libpostal | MIT |
| scipy.constants | scipy | lookup | ⚙ verified | 96 MB | BSD-3 |
| astropy.constants | astropy | lookup | ⚙ verified | 42 MB | BSD-3 |
| pint | pint | convert, compute | ⚙ verified | 1.4 MB | BSD |
| chemformula | chemformula | parse, compute | ⚙ verified | 68 KB | MIT |
| periodictable | periodictable | lookup | ⚙ verified | 2.6 MB | Public domain |
| uncertainties | uncertainties | compute | ⚙ verified | 308 KB | BSD-3 |
| ambiance | ambiance | lookup, compute | ⚙ verified | 76 KB | Apache-2.0 |
| holidays | holidays | temporal | ⚙ verified | 8.2 MB | MIT |
| python-dateutil | python-dateutil | parse, temporal | ⚙ verified | 752 KB | Apache-2.0/BSD |
| workalendar | workalendar | temporal | ⚙ verified | 1.4 MB | MIT |
| iso4217 | iso4217 | lookup | ⚙ verified | 68 KB | Public domain |
| python-stdnum | python-stdnum | validate | ⚙ verified | 4.3 MB | LGPL |
| phonenumbers | phonenumbers | parse, validate | ⚙ verified | 24 MB | Apache-2.0 |
| python-magic | python-magic | parse | ⚙ verified | 32 KB + system libmagic | MIT |
| filetype | filetype | parse | ⚙ verified | 252 KB | MIT |
| tldextract | tldextract | parse | ⚙ verified | 452 KB | BSD-3 |
| user-agents | user-agents | parse | ⚙ verified | 40 KB | MIT |
| skyfield | skyfield | compute, temporal | ⚙ verified | 1.2 MB | MIT |
| ephem | ephem | compute | ⚙ anchor / ⚠ phase bug | small C ext | LGPL |
| sgp4 | sgp4 | compute | ⚙ verified | 704 KB | MIT |
| astral | astral | compute, temporal | ⚙ verified | 244 KB | Apache-2.0 |
| pymeeus | pymeeus | compute, temporal | ⚙ verified | 3.0 MB (sdist only) | LGPL-3.0 |
| colour-science | colour-science | convert, compute | ⚙ verified | 95 MB (76 MB htmlcov artifact) | BSD-3 |
| biopython | biopython | lookup, compute | ⚙ verified | 17 MB | BSD-3 |
| starfile | starfile | parse | ⚙ verified | 40 KB | BSD-3 |
| czml3 | czml3 | generate | ⚙ verified | small | BSD-3 |
| isodate | isodate | parse | ⚙ verified | 160 KB | BSD |
| mimeparse | mimeparse | parse | ⚙ verified | 32 KB | MIT |
| molmass | molmass | compute | ⚙ verified | 288 KB | BSD-3 |
| mido | mido | parse | ⚙ verified | 416 KB | MIT |
| particle | particle | lookup, compute | ⚙ verified | 1.7 MB | BSD-3 |
| geographiclib | geographiclib | compute | ⚙ verified | 260 KB | MIT |
| bizdays | bizdays | temporal | ⚙ verified | 116 KB | BSD |
| charset-normalizer | charset-normalizer | validate | ⚙ verified | 1.1 MB | MIT |
| idna | idna | convert | ⚙ verified | 428 KB | BSD-3 |
| pandas-market-calendars | pandas-market-calendars | temporal | ⚙ verified | 1.1 MB | MIT |
| financedatabase | financedatabase | lookup | ⚙ verified (data fetched) | 100 KB + 20 MB data | MIT |
| chemicals | chemicals | lookup | ⚙ verified | 73 MB | MIT |
| pysweph | pysweph | compute | ⚙ verified | 2 MB | AGPL-2.0 |
| networkx *(auxiliary)* | networkx | — | ⚙ verified | 13 MB | BSD-3 |

## 6. Candidates not yet installed

From research (see conversation 2026-09); none in `pyproject.toml` yet:

| Package | Category | Why not yet |
|---|---|---|
| `pyproj` | geography | CRS / datum transforms (PROJ) — heavier, native |
| `rdkit` | chemistry | SMILES/InChI, fingerprints — **heavy**, native build |
| `thermo` / `fluids` | chemistry | ChEDL compute layer over `chemicals` (installed); heavy, not needed for lookup |
| `pvlib` | astronomy | solar position & irradiance (NREL SPA) — native-ish |
| `music21` | music | note names/scales/score analysis — large |
| `flatlib` / `kerykeion` | astrology | listed in `reference-libraries.md` but not yet installed (Swiss Ephemeris stack; `pyswisseph` replaced by installed `pysweph`) |
| `rfc3987` | formats | IRI parsing — **GPL-3+**, excluded from default install (opt-in candidate) |
| `pysolar` | astronomy | solar position — **GPL**, excluded from default install (opt-in candidate) |

> **Hallucinated packages** — `iana-registries` and `pybusday` do not exist on
> PyPI (both surfaced from AI-generated library lists). Real alternatives for
> business days: `bizdays` (installed) / `pandas_market_calendars` (installed).

## 7. Gotchas (learned while verifying)

1. **`colour` vs `colour-science`** — PyPI name collision; the real package is
   `colour-science` (imports as `colour`). An unrelated toy package owns `colour`.
2. **`postal` triple collision** — `postal` (PyPI) is a *text dedupe* library and
   `pypostal` (PyPI) is a *mail-sending client*; the libpostal bindings are
   `pypostal-multiarch` (OpenVenues rebundle), which also needs the system
   `libpostal.so.1` on the loader path (tests preload it via ctypes).
3. **`pyephem` is a shim** — empty package depending on `ephem`; depend on `ephem`.
4. **ephem 4.2.1 moon bug (2026-09)** — the current wheel returns wrong moon
   positions and an internally inconsistent phase (82.9°) for 2025-06-15 12:00
   UTC on this platform; independent oracles (pymeeus 228.8°, astropy 228.2°)
   agree. `test_ephem_moon_phase` is an xfail canary; the definitional J2000
   Date anchor (`float(Date) = JD − 2415020.0`) still passes.
5. **`tldextract` fetches by default** — first call may hit the network; use
   `TLDExtract(suffix_list_urls=())` for the bundled snapshot.
6. **`colour` wheel ships 76 MB of `htmlcov`** — footprint is mostly a maintainer
   artifact; real code ≈ 19 MB.
7. **`timezonefinder` needs its 63 MB data package** — expect the combined size.
8. **skyfield 1.55** — `ts.utc()` string parsing is broken (use numeric args),
   `Time` has no `.jd` (use `.tt`/`.tai`), and planetary ephemerides must be
   downloaded (the bundled `ephem.bsp` is gone).
9. **Version churn breaks naive assumptions** — stdnum 2.x, periodictable 2.x,
   astral 3.x, workalendar 17 (`workalendar.usa`, `add_working_days`), chemformula
   1.x (`ChemFormula`, properties not methods), czml3 3.x (pydantic) all
   renamed/moved APIs versus older docs. Re-run the suite after every upgrade.
10. **LGPL set**: `pycountry`, `python-stdnum`, `ephem` — fine for internal agent
    tooling; only matters if distributing Poor Richard as a linked product.
11. **ISO 639-3 for German is `deu`** — `ger` is the 639-2/B code; the registry
    records the distinction in the python-iso639 card.
12. **`mimeparse` is abandoned** — last release 2013; `best_match()` is broken on
    py3 (`dict.has_key`). `parse_mime_type` / `parse_media_range` work fine.
13. **`molmass` 2026.x** — the top-level `molmass` name is a *module*, not the
    old callable; use `molmass.Formula('H2O').mass`.
14. **`chemicals` is 73 MB** — pure data (property tables, CAS registry); expect
    the size, no native deps.
15. **`charset-normalizer` cp125x ambiguity** — Windows-125x detection is
    unreliable (cp1252 samples came back as cp1257/cp1250); golden test is
    limited to unambiguous UTF-8/ASCII.
16. **`pandas-market-calendars` pins pandas 2.3.3** — it constrains the resolver;
    `bizdays` (`Calendar.load("PMC/XNYS")`) and `pandas_market_calendars`
    overlap: bizdays for day arithmetic, PMC for session/adjust logic.
17. **GPL exclusions** — `rfc3987` (GPL-3+) and `pysolar` (GPL) are documented
    opt-in candidates, not in the default install; the LGPL set (item 10) is
    the license floor.
18. **`pysweph` is AGPL-2.0 and not a drop-in for `pyswisseph`** — accepted for
    this project on maintainer decision (network-copyleft only matters if
    offering it as a network service). API breaks: `calc_ut` returns
    `(results, retflags, warning_str)`, flags are `FLG_*`, results is a 6-tuple.
    Without the `.se1/.se2` data files it falls back to the built-in Moshier
    ephemeris (arcsecond-class — cross-checked vs astropy/JPL to <2″); the
    fallback is announced in the returned warning string.
19. **`pymeeus` module/class name collision** — `from pymeeus import Sun`
    imports the *module*; the class is `pymeeus.Sun.Sun` (same for `Moon`),
    and `Epoch` comes from `pymeeus.Epoch`. `Angle` objects convert via
    `float()`. Epoch defaults to TT; `utc=True` applies TT−UTC = 69.184 s for
    2025 (its leap table is frozen at 2017 — still correct until the next
    leap second; pass `leap_seconds=` beyond that).
20. **`ambiance` takes geometric height, ISA tables use geopotential** —
    `Atmosphere(h)` converts internally via `H = h(1 − h/R)` (R = 6356.766 km),
    so the ISA table value at "11 km" (22632 Pa, 216.65 K) is reached at
    11019 m *geometric* input. Properties return numpy arrays (`[0]` for
    scalar input); `from_pressure()`/`from_density()` invert the profile.
