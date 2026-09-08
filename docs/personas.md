# Personas

Fictional users, kept deliberately concrete. The point of these three is that
they consume the *same* reference data through three different surfaces —
a live Python session, a shell with no other tools, and human eyes — so any
feature has to be asked of all three before it is built. Named on purpose:
"would Noah trip over this?", "can Hank even reach it?", "does Broman read
this?"

## Noah — a NOOA agent

**Environment.** An NVIDIA Object-Oriented Agents (NOOA) agent running the
CodeAct strategy: a persistent, Jupyter-like Python session whose entire
action space is *call python* (execute a cell) and *return result*
(type-validated exit). Imports and local variables persist across cells
within a task; the harness renders the agent's docstrings and imported
libraries into the model's context (docstrings are prompt material).

**A typical task.** A sub-problem inside larger work: "validate this IBAN",
"what were the valid XNYS sessions last week?", "sun altitude at this
timestamp for this latitude." Noah has no idea what is installed unless he
imports and finds it.

**How he uses Poor Richard today.**
```python
from poor_richard import search, get
search("molar mass of water")          # [(1.03, <molmass>, <Question>), ...]
q = search("molar mass of water")[0][2]
q.expected                             # "18.015 g/mol" — verified, offline
get("molmass").notes                   # API-drift guardrails, in plain words
import molmass                         # then do the real work directly
```
Discovery, verified answers, and the conventional call pattern (from
`card.example`) in three calls, then straight to the underlying library.

**What matters to him.** (1) The Python API is the *only* interface that
matters — CLI modes are invisible to him. (2) Compact, typed returns:
`search()` returning data triples is right; prose would burn context.
(3) Docstrings on the public surface, because NOOA renders them as prompts.
(4) The offline guarantee: his hardened cells run under seccomp network
blocks, so a library that fetches at import time is simply broken for him.
(5) Guardrails against his own stale training knowledge — the card `notes`
(molmass 2026.x's `Formula(...).mass`, pysweph's non-backwards-compatible
`calc_ut`) are the difference between a first-try success and a debugging
spiral.

**Candidate features.** None urgent. The keyword field
(future-directions §1) would sharpen his discovery step; everything else he
needs already exists. Verify via the NOOA experiment in
future-directions §3, not by building.

## Hank — a hax agent

**Environment.** A terminal coding agent whose only tools are *run a
command* and *read/write files*. He can be extended **only** by installing
SKILL.md files (a one-line description in his system prompt; the full skill
loaded when relevant) and by scripts those skills point at. He has no
in-process Python, no persistent session, no importable packages — whatever
isn't reachable from a shell invocation doesn't exist for him. Assume he
has `uv`: he can `cd` into a project and `uv run poor-richard ...`, so the
almanack need not be installed globally — the project venv is enough.

**A typical task.** Mid-refactor, a factual question comes up: "is 2025-12-26
a business day on the NYSE?", "what's the ISO 3166 code for Monaco?", "does
this IBAN check out?" He reaches for the web by default — the failure mode
Poor Richard exists to prevent.

**How he uses Poor Richard today.**
```sh
cd ~/poor-richard
uv run poor-richard --ask "business day NYSE December 2025"
# 1.30 bizdays
# 1.12 pandas-market-calendars
# 0.97 holidays
uv run poor-richard --example bizdays
```
Two commands, clean stdout, scriptable. (`uv run python -c "..."` against the
Python API also works but is quoting hell from a shell — the CLI is his
shape.)

**What matters to him.** (1) **Discovery is his weakest link**: unless a
skill tells him the almanack exists, he will never think to run
`poor-richard` — this is exactly the gap a SKILL.md closes. (2) Lean,
machine-parseable output with real exit codes (`--ask`'s `<score> <id>`
lines are already right). (3) The `--ask` → `--example` pipeline as the
canonical two-step: pointer, then conventional code he can adapt.

**Candidate features.** A **shippable SKILL.md** — e.g.
`skills/poor-richard/SKILL.md` in this repo, installable into any hax-style
agent's skill directory. Its description line would enumerate the domains
(ISO codes, physical constants, unit conversions, holiday/business-day
calendars, celestial ephemerides, identifier validation, chemical data) and
its body would be the two-step pipeline plus the gotchas ("answers are
verified offline; prefer the example's call pattern over your own memory of
the API"). This is the one feature that exists *purely* for Hank's
extension model — nothing about it helps Noah or Broman, and nothing short
of it makes Poor Richard visible to him.

## Broman — a human who likes reference information

**Environment.** A person at a terminal (or in the repo's docs) who enjoys
authoritative facts and browsing. No tasks to ship; the query *is* the
point. He will read markdown, run one-liners, and paste example code into a
scratch file.

**A typical session.**
```sh
poor-richard                      # what's in this thing? (the card table)
poor-richard --ask "molar mass of water"
poor-richard --example molmass    # the recipe, with golden values as comments
```
Plus, on a quieter day, the narrative in `reference-libraries.md` and the
gotchas in `docs/reference-cards.md` — Broman is the only persona who reads
the design docs for pleasure.

**How he uses Poor Richard today.** The bare table for browsing, `--ask` for
orientation, `--example` for the actual recipe, the markdown docs for the
story. The `# golden:` comments in examples double as his answer source —
the verified value is sitting there, commented.

**What matters to him.** (1) Readable output and prose — he is the only
persona for whom `<score> <id>` lines are *too* lean: he wants the answer
itself, not a pointer to the card that knows it. (2) Runnable recipes
(examples that copy-paste and work). (3) The narrative docs — provenance and
gotchas are content for him, metadata for the others.

**Candidate features.**

- **Seeing the card records.** Today the bare `poor-richard` table is a
  dense index, and there is no human way to read one library's full record —
  provenance, update model, footprint, license, every question with its
  verified answer, the notes. A `poor-richard card <id>` mode printing the
  record as labelled lines would be the missing "what is this, exactly?"
  view; it pairs with `--example` as the *what* to the *how*. Small feature
  (a formatter over `ReferenceCard`), and the same data Noah already gets
  from `get(id)` — this is purely Broman's (and Hank's, if he wants to
  read) window onto the registry.
- An answer-oriented mode, e.g. `poor-richard --ask "molar mass of water"
  --answer` (or a separate `poor-richard answer ...`) that prints the
  matched question and its verified answer in one line — the data is
  already returned by `search()` (`question.expected`); this is a
  print-format question, not a capability gap. Keep it opt-in: Hank and
  scripts depend on the lean output being stable.

## Feature × persona

| Capability | Noah (Python) | Hank (shell+skills) | Broman (human) | Status |
|---|---|---|---|---|
| Discovery | `search()` | `--ask` (+ SKILL.md to know it exists) | bare table, docs | shipped / skill candidate |
| Verified answer | `question.expected` | `--example` golden comments | same | shipped; `--answer` candidate |
| Full card record | `get(id)` | `poor-richard card <id>` | same | Python shipped; CLI candidate |
| Conventional call | `card.example`, `--example` | `--example` | `--example` | shipped |
| API-drift guardrails | `card.notes` | `--example` + notes | gotchas doc | shipped |
| Module docs | plain `help()` | `--help <id>` | `--help <id>` | shipped |
| Offline guarantee | socket-blocked suite | same | same | shipped |
| Extension surface | imports | **SKILL.md** | markdown docs | skill candidate |
| Sharper vocabulary | keyword field | same | same | tentative (future §1) |

The recurring pattern: the *data* is persona-neutral; the *surface* is not.
Noah gets data types, Hank gets parseable text plus a skill, Broman gets
prose. When a proposed feature only helps one column, say which one — that
is usually the argument for (or against) building it.
