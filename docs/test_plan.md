# Test plan: the almanack with real agents and users

**Purpose.** Smoke-test the value proposition with actual consumers: can a
tester, given a factual task and *no hint about which library to use*,
(a) discover the right tool, (b) call it conventionally on the first attempt,
and (c) get the correct, authoritative answer — fully offline? This is not a
benchmark and produces no leaderboard; it produces a list of concrete misses
that feed the keyword field (future-directions §1) and the card-text
discipline.

**Testers** (see `docs/personas.md`):

- **Noah** — NOOA CodeAct agent: persistent Python session, `call python` /
  `return result`. Setup: wheel installed in his environment; he may import
  anything that is installed.
- **Hank** — hax-style terminal agent: commands + files only, `uv` available.
  Setup: he is told the project exists at `~/poor-richard` and may `uv run`
  in it. No SKILL.md exists yet — his discovery is tested *cold* (that is
  the point; a later run with the skill installed is the A/B).
- **Broman** — human at a terminal. Setup: pointed at the README. He works
  however he likes (CLI, `python -c`, docs); we record what he actually did.

**Ground rules for every run.**

1. Fresh session, no prior context about Poor Richard or its libraries.
2. The task statement never names a library.
3. Expected results below are verified offline against the same libraries
   (same pinned versions) as the golden test suite. The questions deliberately
   use *non-canonical* inputs — no standard examples, no trivia values — so
   recall alone cannot substitute for computation. Once a live run confirms an
   expected value, promote the question to a verified question in the registry
   (same feedback loop as the "why" list below).
4. Network availability is noted per run; the almanack's claim is that none
   of it is needed. A tester who fetches the web still "answers" — we score
   that separately (see grid).

## Tasks

Each task is **one question with one answer**. Inputs are deliberately
non-canonical (not the standard's own examples, not trivia values) so the
question must be *computed*, not recalled.

### T1. The 10th trading day (calendars)

> "What is the 10th NYSE trading day after 2025-12-22?"

- **Cards exercised:** bizdays, pandas-market-calendars, holidays
- **Expected:** 2026-01-07 (skips Christmas, both weekends, and New Year's Day)
- **Why this task:** counting business days across a holiday + weekend +
  year-end interaction is a classic hallucination; also the strongest
  multi-library card cluster (three cards can answer it — the tester should
  find any of them).

### T2. A checksum that looks valid (identifier validation)

> "Is IBAN DE13430609671234567891 valid? Show your working."

- **Cards exercised:** python-stdnum
- **Expected:** no — the mod-97 check fails; the correct check digits for
  this BBAN are 13
- **Why this task:** a well-formed IBAN with a one-off check digit cannot be
  answered by pattern recall — it is mod-97 arithmetic or nothing, and
  "show your working" forces the real computation over "looks valid".

### T3. A hydrate's molar mass (constants & chemistry)

> "What is the molar mass of copper(II) sulfate pentahydrate (CuSO4·5H2O) in
> g/mol, using IUPAC atomic weights?"

- **Cards exercised:** molmass (or chemformula)
- **Expected:** 249.685 g/mol (±0.01)
- **Why this task:** the hydrate dot-notation trips formula parsers, and the
  value is not a memorized constant — it is 21 atoms summed.

### T4. The Rydberg constant (constants)

> "What is the Rydberg constant in m⁻¹? Report the value you used and its
> precision."

- **Cards exercised:** scipy.constants
- **Expected:** 1.0973731568157e7 m⁻¹ (±0.01%)
- **Why this task:** a named constant nobody has memorized — fuzzy recall
  ("~1.1e7") is outside the tolerance, and "report its precision" exposes a
  value the tester invented rather than read.

### T5. Cape Town to Nairobi, on the ellipsoid (geodesy)

> "What is the geodesic distance over the WGS84 ellipsoid between Cape Town
> (33.9249°S, 18.4241°E) and Nairobi (1.2921°S, 36.8219°E)? State the method."

- **Cards exercised:** geographiclib
- **Expected:** ≈ 4089.5 km (golden: 4,089,525 m, ±1 km)
- **Why this task:** a city pair whose distance is not trivia; the spherical
  haversine answer is ~0.3% off (~12 km), so the tolerance makes the method
  matter, and "state the method" exposes it.

### T6. Where is the sun? (ephemeris)

> "What is the Sun's geocentric ecliptic longitude at 2025-06-15 12:00 UTC?"

- **Cards exercised:** pysweph (or astropy/ephem/skyfield)
- **Expected:** ≈ 84.64° (a few days before the solstice's 90°)
- **Why this task:** ephemeris math from memory is impossible; only a real
  computation gets here. Deliberately *not* the moon — the ephem 4.2.1
  moon bug (xfail canary) is a known hazard, and muddying the task with it
  would test the bug, not the almanack.

### T7. A Korean domain (encodings)

> "What is the ASCII-compatible (IDNA/punycode) encoding of the domain
> 한국.kr?"

- **Cards exercised:** idna
- **Expected:** xn--3e0b707e.kr
- **Why this task:** punycode by hand is a hallucination magnet; the domain
  is deliberately *not* the RFC's canonical example (例え.jp), so the answer
  cannot be recalled.

### T8. A two-part TLD (encodings)

> "What is the registered top-level domain (public suffix) of
> 'app.example.org.cn'?"

- **Cards exercised:** tldextract
- **Expected:** org.cn
- **Why this task:** multi-part TLDs trip naive `split('.')` reasoning, and
  org.cn is a less common suffix than co.uk, so it is not a memorized answer.

### T9. What kind of thing is Deere? (financial classification)

> "According to the financedatabase classification, what sector and industry
> is Deere & Company (DE) in?"

- **Cards exercised:** financedatabase
- **Expected:** Industrials / Machinery
- **Why this task:** the classification is dataset-specific — other taxonomies
  list Deere as Consumer Cyclical — so the answer is not recallable; also
  tests the one card whose data must be pre-fetched (a setup-failure here is
  a *test-environment* finding, not a tester failure) and, as the
  heaviest-dependency card, doubles as an install-size probe.

### T10. Add a duration to a date (temporal parsing)

> "Parse the ISO 8601 duration P1Y2M3DT4H5M6S and add it to 2025-01-01
> 00:00 (calendar arithmetic: years to years, months to months, then the
> remainder). What date and time do you land on?"

- **Cards exercised:** isodate (plus dateutil for the arithmetic)
- **Expected:** 2026-03-04 04:05:06
- **Why this task:** the isodate Duration API shape (years/months/days ints,
  `seconds` = total time-seconds) is exactly the kind of version-churn
  trap the card `notes` exist for — first-try convention is the metric.

## Scoring grid

Score each run per task on four points; a "clean pass" is 4/4.

| Point | Question |
|---|---|
| **Correct** | Answer matches the expected value within stated tolerance |
| **Conventional** | First attempt used the library's pinned API shape (no trial-and-error against version churn) |
| **Discovered** | Reached the right library via the almanack (`search`/`--ask`/cards/docs), not by guessing the package name from training data |
| **Offline** | No network fetch was needed or made |

Record per run: the transcript, the exact calls/commands used, and which
point failed and *why* (wrong value / wrong API / wrong library / fetched
the web). The aggregate of the "why"s is the deliverable — it is the
prioritized trigger list for card-text fixes and the keyword field.

## Known hazards (environment, not tester)

- **financedatabase data** must be pre-fetched (`scripts/fetch_financedatabase.py`)
  or T9 is unanswerable offline; on a fresh NOOA environment this is the most
  likely setup failure.
- **ephem 4.2.1 moon bug** — any task drift toward lunar positions can
  surface the xfail canary; steer testers back to T6's sun or to astropy.
- **The SKILL.md exists in the repo but is not installed into the test
  agent's skill directory** — run Hank cold first (no skill), then warm
  (skill installed); that A/B measures the skill's discovery value. Record a
  cold failure distinctly from "found the almanack but picked the wrong card".
- **First-run cost** — the full base dependency set (see `pyproject.toml`)
  makes fresh-environment setup slow;
  pre-build the wheel and venv before the session starts, and note the wall
  time anyway (it is a real adoption number).

## Execution notes

- One task per fresh session; do not let a run carry context into the next.
- Give Broman the README and 10 minutes per task; give the agents the task
  statement only.
- Keep raw transcripts — the "how did you find it" narrative is worth more
  than the pass/fail column.
