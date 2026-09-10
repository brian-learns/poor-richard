# Adding a Python library to the almanack

Step-by-step for adding a new reference library. The *why* (archetypes,
evaluation axes, card schema, golden-question method) lives in
[reference-cards.md](reference-cards.md); this is the *how*.

If the suite is already red when you start (a previous run died halfway
through), stop and report it — don't fix unrelated failures or build on
top of them.

## 0. Verify the package is real

AI-generated library lists contain hallucinations — `iana-registries` and
`pybusday` both looked plausible and do not exist on PyPI. Before anything
else:

- If the task came from a `docs/new/<name>.txt` queue file, the filename is
  a hint, not authority — the real name comes from this step (the
  `email-valadator` queue file is `email-validator` on PyPI).
- Confirm the project page exists and is maintained (recent release, live
  repo, non-abandoned author).
- Confirm you have the **right PyPI name**. Name collisions have bitten this
  project three times: `colour` (toy package; the real one is
  `colour-science`), `postal`/`pypostal` (unrelated; the libpostal binding is
  `pypostal-multiarch`), and `pyephem` (empty shim over `ephem`).
- Note the license now — it decides whether this is even allowed (step 1).

## 1. Curation decision

Evaluate against the axes in reference-cards.md §2, concretely:

| Question | Look for |
|---|---|
| **Archetype fit** | Does it answer lookup / parse / convert / compute / validate / temporal / generate questions? If it's only a *working tool* (no reference data), it's an auxiliary at best. |
| **Provenance** | Where does the data come from? Official standards (ISO, IANA, PDG, CODATA) are gold; maintainer-curated data is acceptable but must be said so on the card. |
| **Update model** | `ALGORITHMIC` (derived, stable), `SNAPSHOT` (bundled data, re-verify on upgrade), or `LIVE` (fetches — usually a disqualifier, see below). |
| **Offline** | Does the golden path work with the network blocked? Libraries that fetch at *import time* fail the suite by design. Data that must be fetched **once** and then read locally is fine (pattern in step 5). |
| **License** | Permissive (MIT/BSD/Apache): fine. LGPL: fine for internal tooling (pycountry, stdnum, ephem). **GPL: excluded** from the default install (rfc3987, pysolar) — document as opt-in candidate. **AGPL: requires explicit maintainer sign-off** (pysweph was accepted deliberately). |
| **Footprint** | Code size *plus* bundled data *plus* notable transitive deps. Measure, don't guess (`du -sh` on the site-packages dir; `importlib.metadata` for `Requires-Dist`). financedatabase is the cautionary tale: 100 KB of code that drags in scikit-learn + yfinance. |

If it fails, don't install it — record it in the "candidates not installed"
section of reference-cards.md §6 with the reason, and (if it came from
`reference-libraries.md`) mark the entry there.

## 2. Install

```sh
uv add <pypi-name>        # never `uv pip install` — pyproject.toml is the
                          # record of what the almanack depends on
```

The registry integrity test enforces 1:1 sync between `pyproject.toml`
dependencies and cards, so the next step is mandatory, not optional.

Sdist-only packages (pymeeus) build from source on `uv add` — a slow or
noisy build is not a failure.

## 3. Golden questions

Pick 1–5 questions spanning the library's archetypes. Rules:

1. **Expected values come from the standard, not the package docs.** The
   IBAN spec's own example, CODATA constants, the IANA tz database, "the
   solstice is at 90° ecliptic longitude" — anything independently known.
   If the only source of the value is the library itself, it's a stability
   check, not a golden question; say so in the comment.
2. **Cross-check against an oracle already in the tree** when one exists —
   e.g. pysweph's sun position vs astropy/JPL, bizdays vs
   pandas-market-calendars. Two independent libraries agreeing to the arcsecond
   is the strongest verification we have.
3. **Tight tolerances for floats** (the value is the point), exact matches
   for discrete data.
4. Write the call down *as you discover it*. Version churn is the #1
   breakage mode (isodate's Duration shape, molmass 2026.x's
   `Formula(...).mass`, workalendar 17's moves) — the test is the record of
   the API at the pinned version.

## 4. The test

Append to `src/poor_richard/tests/test_golden.py`:

```python
def test_<card_id>():
    import <module>          # imports INSIDE the function: a library that
                             # fetches at import time must fail loudly here
    ...
    assert ...
    assert _expected("<card_id>", "<question>") == "<expected>"   # one pin per question
```

Conventions:

- The autouse `no_network` fixture in `tests/conftest.py` blocks sockets for
  every test — a PASS means correct **and** offline. Don't weaken it.
- **Pin the registry answer.** One `_expected(card, question)` assert per
  verified question, in the same test, tying the card's `expected` string to
  the value you just proved (reference-cards.md §4, "Answer pinning"). This
  is what catches a registry data edit that drifts from the standard — the
  pycountry alpha-3 bug slipped through because nothing compared the two.
- **Data-dependent libraries** (system libs, one-time downloads): *skip* when
  the data is absent, never fetch in the test. Precedents: `test_postal`
  (skips without system `libpostal.so.1`) and `test_financedatabase` (skips
  without the fetched CSVs). Ship a fetch script in `scripts/` and document
  it on the card.
- **Known upstream bugs**: keep a passing anchor test plus an `xfail` canary
  named after the bug (`test_ephem_moon_phase`). When the upstream fixes it,
  the canary flips to XPASS and yells at you.
- Never `print()` a whole table (financedatabase's no-arg `search()` returns
  112k rows and OOM-killed a shell).

## 5. The card

Add a `ReferenceCard` to `src/poor_richard/registry.py` (grouped by domain):

| Field | Notes |
|---|---|
| `id` | stable slug, usually the import name |
| `pypi` / `import_name` | both — they often differ (`colour-science` → `colour`) |
| `archetypes` | from the decision in step 1 |
| `provenance` | where the data comes from, with numbers (counts, standards) |
| `update_model` | `_U.ALGORITHMIC` / `_U.SNAPSHOT` / `_U.LIVE` |
| `offline` / `offline_verified` | verified = golden test passed under the socket block |
| `footprint` / `native_deps` | measured, including data |
| `license` | exact (AGPL-2.0, not "AGPL") |
| `questions` | one `Question` per golden question; verified ones need `test_id` |
| `notes` | **the gotchas**: API breaks, name collisions, data placement, fallbacks. This is where the card earns its keep. |
| `keywords` | to aid in the discovery of the library  |
| `example` | only if the derived example is awkward (fixtures, system libs) — see reference-cards.md "Tests double as usage examples". Otherwise leave empty; `poor-richard --example` derives it from the test. |

### 5.1 Keywords

1. **Examine the library.** Import it and play with it in `.venv/bin/python`:
   the module docstring, public members, and — most importantly — the
   **standards, units, and identifiers in its data**. High-value terms live in
   the domain data (e.g. `celsius` in pint's unit registry, `luhn` in
   stdnum's validators), not in API names or docstrings.

2. **Pick 5 tokens.** Quality bar, in order:
   - A person would actually type it: standard names/numbers, unit names,
     identifier types (iban, isbn, vin, ean), colloquial domain words
     (sunrise, checksum, solstice).
   - Not already in your card's existing text 
   - Not generic filler: `data`, `convert`, `number`, `date`, `library`,
     `validate`, `calculation` are useless on their own.
   - Lowercase, singular (search folds plurals), space-separated.

## 6. Docs

- `docs/reference-cards.md` §5: add a row to the card table, bump the count.
  If the library produced a lasting gotcha, add it to §7.
- `reference-libraries.md` (in the repo root, not `docs/`): add/refresh the narrative entry in the matching
  section, with the source link and the `uv add` name.
- If the library was previously listed in `docs/reference-cards.md` §6
  (candidates not installed) or the `reference-libraries.md` candidates
  section, remove that row — it's installed now.

## 7. Verify

```sh
uv run pytest                     # full offline suite, including integrity
uv run poor-richard               # table shows the new card
uv run poor-richard --example <id>  # example derives (or curated) correctly
uv run poor-richard --help <id>   # help() resolves through the card
uv run poor-richard --ask "<domain word>"  # the new card surfaces in search
uv build                          # wheel still builds (tests ship inside)
```

The integrity tests do most of the checking for you: unique ids, importable
names, verified-question↔test linkage, answer pinning, pyproject↔card sync,
example availability.

## 8. Commit

One commit: `uv add`'s pyproject/lock changes, the test, the card, the docs.
Commit only after the full suite is green — a partial state (dependency
added, no card yet) leaves the repo red for the next run. Message pattern:
`Add <pkg>: <one-line what/why>` with the interesting findings in the body
(API breaks, data requirements, license decisions).
