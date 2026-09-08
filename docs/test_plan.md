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
3. Expected results below are the registry's *verified* golden values — the
   test plan and the test suite share their source of truth.
4. Network availability is noted per run; the almanack's claim is that none
   of it is needed. A tester who fetches the web still "answers" — we score
   that separately (see grid).

## Tasks

### T1. The week around Christmas (calendars)

> "In the week of 2025-12-22 to 2025-12-31, which days are valid trading
> sessions on the NYSE? And if a trade settles on Christmas Day itself, what
> is the next business day?"

- **Cards exercised:** bizdays, pandas-market-calendars, holidays
- **Expected:** sessions 24, 26, 29, 30, 31 (no 25th, no weekends); 12-25 → 12-26
- **Why this task:** holiday + weekend interaction is a classic
  hallucination; also the strongest multi-library card cluster (three cards
  can answer it — the tester should find any of them).

### T2. The checksum gauntlet (identifier validation)

> "Which of these pass their standard checksums: IBAN
> DE89370400440532013000, card number 4111111111111111, ISBN-13
> 978-3-16-148410-0? Show your working."

- **Cards exercised:** python-stdnum
- **Expected:** all three valid (each is the standard's own canonical example)
- **Why this task:** LLMs are notoriously bad at multi-step checksum
  arithmetic; "show your working" forces real computation over pattern
  recall.

### T3. How heavy is glucose (constants & chemistry)

> "What is the molar mass of glucose (C6H12O6) in g/mol using IUPAC atomic
> weights? Also: what is the exact speed of light in m/s?"

- **Cards exercised:** molmass, scipy/astropy constants
- **Expected:** 180.156 g/mol (±0.01); 299,792,458 m/s (exact by definition)
- **Why this task:** two archetypes in one (compute + lookup); the exact
  constant checks whether the tester reports *defined* values or fuzzy
  remembered ones.

### T4. Paris to London, on the ellipsoid (geodesy)

> "What is the geodesic distance over the WGS84 ellipsoid between Paris
> (48.8566°N, 2.3522°E) and London (51.5074°N, 0.1278°W)? State the method."

- **Cards exercised:** geographiclib
- **Expected:** ≈ 343.9 km (golden: 343,923 m)
- **Why this task:** models routinely answer with the spherical
  haversine distance, which is ~0.3% off — the tolerance makes the method
  matter, and "state the method" exposes it.

### T5. Where is the sun? (ephemeris)

> "What is the Sun's geocentric ecliptic longitude at 2025-06-15 12:00 UTC?"

- **Cards exercised:** pysweph (or astropy/ephem/skyfield)
- **Expected:** ≈ 84.64° (a few days before the solstice's 90°)
- **Why this task:** ephemeris math from memory is impossible; only a real
  computation gets here. Deliberately *not* the moon — the ephem 4.2.1
  moon bug (xfail canary) is a known hazard, and muddying the task with it
  would test the bug, not the almanack.

### T6. A Japanese domain and a UK TLD (encodings)

> "What is the ASCII-compatible encoding of the internationalized domain
> 例え.jp? And what is the registered top-level domain of
> 'shop.example.co.uk'?"

- **Cards exercised:** idna, tldextract
- **Expected:** xn--r8jz45g.jp; co.uk
- **Why this task:** punycode by hand is a hallucination magnet, and
  multi-part TLDs (co.uk) trip naive `split('.')` reasoning.

### T7. What kind of thing is AAPL? (financial classification)

> "According to the financedatabase classification, what sector is Apple
> (AAPL) in? And in the FX pair EUR/USD, which currency is the base and
> which the quote?"

- **Cards exercised:** financedatabase
- **Expected:** Information Technology; EUR base / USD quote
- **Why this task:** tests the one card whose data must be pre-fetched — a
  setup-failure here is a *test-environment* finding, not a tester failure;
  also the heaviest-dependency card, so it doubles as an install-size probe.

### T8. Add a duration to a date (temporal parsing)

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
  or T7 is unanswerable offline; on a fresh NOOA environment this is the most
  likely setup failure.
- **ephem 4.2.1 moon bug** — any task drift toward lunar positions can
  surface the xfail canary; steer testers back to T5's sun or to astropy.
- **Hank has no SKILL.md yet** — cold discovery may fail for him purely for
  lack of a pointer; that failure mode is the justification for the skill,
  so record it distinctly from "found the almanack but picked the wrong card".
- **First-run cost** — 43 dependencies make fresh-environment setup slow;
  pre-build the wheel and venv before the session starts, and note the wall
  time anyway (it is a real adoption number).

## Execution notes

- One task per fresh session; do not let a run carry context into the next.
- Give Broman the README and 10 minutes per task; give the agents the task
  statement only.
- Keep raw transcripts — the "how did you find it" narrative is worth more
  than the pass/fail column.
