# Two-stage retrieval (design)

A response to `docs/hypothesis.md`. Status: **building the additive slice**.
The project's bar for promoting a proposal to work is a repeated, concrete
miss (`docs/future-directions.md`), and that miss is now on record: in NOOA
traces the agent stalls on discovery — it does not map the question to a
catalog class, burns turns on `--ask`/keyword misses, and only eventually
falls back to the installed libraries. Correct, but inefficient. That is the
concrete miss this design addresses, so the additive slice is being built. A
full NOOA run remains the *re-validation* that the two-stage affordance
actually reduces the stalls.

## The problem

The reference librarian never pastes the patron's verbatim question into the
card-catalog box. They **parse** it first — "this is a lookup, in the
country-codes class" — and *then* retrieve. The catalog's classification
scheme is what makes that parse possible and checkable.

Poor Richard's present affordances collapse that into one step.
`poor-richard --ask "<question>"` (and `search(query)`) *accepts* a
natural-language question, which promises understanding, but *implements*
keyword matching (`registry.py`, `search()` — bag-of-words over card text, no
semantics). And SKILL.md names it the **canonical** flow:

> Canonical flow: `--ask "<question>"` to find the card, then
> `--example <id>`.

So the documented path invites the agent to treat the almanack like a
chatbot — paste the sentence, get a rank — and to skip the analysis a
librarian would do. That contradicts the project's own stated division of
labor (future-directions §1): *understanding is the agent's job; grounding is
the almanack's.* The interface tempts exactly the behavior the design wants
to avoid.

## The principle

Make the interface's **input contract match its actual capability**. The
agent supplies the *analyzed form* — a catalog class plus key terms — not the
raw sentence. The almanack supplies the **catalog**: the classification
scheme and the *shape* of each reference's questions, so the agent can do the
analysis and check it against the collection.

Two stages:

1. **Classify** — the agent maps the question to a class (archetype) and
   reads the question shapes of the references in that class.
2. **Retrieve** — the agent picks the reference and uses its conventional
   call and verified answer.

The almanack serves the catalog and the reference; it does not understand the
question. The agent does the understanding. That is the whole design.

## API-first

The stable core is the **registry data model plus the retrieval functions**
(`search`, `get`, `by_pypi`, `CARDS`, and the `ReferenceCard`/`Question`/
`Archetype` dataclasses). The CLI is a presentation shell over them.

That ordering is deliberate and it changes what is allowed to move:

- **Stable (behavior pinned):** `search()` ranking, `get()`/`by_pypi()`,
  `CARDS`, the data model. This is the grounding layer the agent and the
  NOOA harness rely on (future-directions §3). Its tests stay green.
- **New (additive):** the stage-1 affordance (below).
- **Free to redesign:** the CLI. Once every command is just
  `print(<api call>)`, the CLI can be reorganized around the two stages
  without touching the core. The CLI-output tests
  (`test_console_ask`, `test_console_script_runs`) are rewritten to match;
  they are not a design constraint.

The earlier "don't break the CLI" framing was the right *scoping* instinct
aimed at the wrong layer. The sacred surface is the API; the CLI is
disposable.

A field observation reinforces the ordering: the shell-only agent (hax)
sometimes skips the CLI entirely and drives the package with inline Python
heredocs. When that happens the API is the *only* surface in play — which is
another reason the two-stage affordance has to live in the API first. The CLI
is where a human (or a well-behaved agent) lands; the API is where the agent
actually goes.

## The two stages, in the API

### Stage 1 — classify: survey the catalog

New:

```python
browse(archetype: Archetype | None = None) -> list[ReferenceCard]
catalog(archetype: Archetype | None = None) -> str   # rendered view of browse()
```

`browse()` returns the references, optionally filtered to one class. The
agent reads each card's `.archetypes` and — crucially — the *shapes* of its
golden questions (`Question.question`, **not** `Question.expected`). The
question shapes are the cataloging practice: they say "this reference answers
questions of the form X." Reading them is how the agent confirms its
classification and disambiguates *within* a class.

`catalog()` renders the same view as text (archetype headers, cards under
them, question shapes, no answers) so the CLI and a Python session both get
one "here is the collection, organized by class" artifact.

The key discipline: **stage 1 shows question shapes, never answers.**
Answers are the prize and belong to stage 2. "Find the book" vs. "read the
book."

Why a dedicated function rather than `[c for c in CARDS if …]`? The data is
already reachable through `CARDS`; the function earns its place on two
counts. First, the name *is* the affordance — `browse()` tells the agent
"survey the stacks," which a list comprehension does not. Second, in NOOA the
docstring is prompt material the model reads (future-directions §3), so the
"reference librarian, stage 1" framing lives where the agent will actually
see it.

### Stage 2 — retrieve: read the reference

`get(id)` / `by_pypi(name)` → card. `example(id)` returns the conventional
call with the verified answer — the card's curated snippet, or its golden
test re-emitted with the assertions as `# golden:` comments (same source as
`poor-richard --example <id>`). This is where the answer is revealed.
`example()` is a new thin accessor: the `card.example` field holds only the
curated override (5 of 55 cards), so the derived-from-test snippet is
surfaced via the function, not the field.

### Fallback — fuzzy search

Unchanged: `search(query, top)` → `(score, card, matched_question)`. It is the
path for when the agent **cannot** cleanly classify — "I don't know what
class this is." Input should be *key terms*, not the user's sentence; it is
keyword matching over the catalog vocabulary, not a chatbot. This is the
"encourage, don't enforce" decision made concrete: `browse` is the
encouraged path, `search` is the available escape hatch, and nothing stops
the agent from taking it.

### The flows

Confident classification (the encouraged path):

```python
from poor_richard import browse, example, get, Archetype

for card in browse(Archetype.LOOKUP):      # stage 1: survey the class
    ...   # agent reads card.questions shapes, picks the match
card = get("pycountry")                    # stage 2: retrieve
print(example(card.id))                    # verified call + answer
```

Uncertain (the fallback):

```python
from poor_richard import search

score, card, question = search("country code")[0]   # key terms, not a sentence
```

## The CLI as a thin wrapper

Every command is a wrapper over the API; the CLI is free to be reshaped
around the two stages. Current → proposed mapping (shape is open, see
*Open*):

| Command | Wraps | Role |
|---|---|---|
| `poor-richard` | `catalog()` | stage 1: the collection by class |
| `poor-richard --archetype <a[,b…]>` | `catalog(Archetype.<a>)` | stage 1, filtered |
| `poor-richard --example <id…>` | `example(id)` | stage 2 (CLI unchanged) |
| `poor-richard --ask <terms>` | `search(terms)` | fallback (demoted) |

`--ask` is kept (it is the CLI face of the load-bearing `search()`), but it is
no longer the canonical flow in the docs, and its argument is framed as key
terms.

## SKILL.md — where the reinforcement lives

The interface reshaping is the non-ignorable nudge, but the *reinforcement*
is mostly narrative, because SKILL.md is what the agent reads. The rewrite:

- Lead with the reference-librarian framing and the two stages.
- Make **stage 1 → stage 2** the canonical flow, shown in both the Python API
  (primary, per future-directions §3) and the CLI (shell-only persona).
- Demote `--ask` / `search` to the fallback, with the "key terms, not the
  user's sentence" contract.
- Keep the existing guardrail prose (prefer the example's call pattern over
  memory; `# golden:` values are authoritative) — that part is already right.

## Decisions recorded

- **Encourage, don't enforce.** `search()` stays available; nothing gates the
  agent into `browse()`. Rationale: `search()` is the NOOA-facing API and the
  test surface, and enforcement kills the human one-liner.
- **No new data this phase.** No `domain` field. The 7 archetypes encode
  *shape*, not *domain* — "lookup" spans country codes and chemical elements
  — so within a class the agent disambiguates by reading question shapes.
  Add a `domain` field only if the NOOA run shows the agent mis-classifying
  *within* an archetype.
- **Additive stage-1 affordance.** `browse()`/`catalog()` are new; the core
  is untouched.
- **Stage-1 API shape.** Two functions, not one:
  `browse(archetype=None) -> list[ReferenceCard]` (flat, for programmatic
  agents) and `catalog(archetype=None) -> str` (rendered, for the CLI/REPL).
  Two because the CLI wants the string and a NOOA-style agent wants the cards.
- **CLI scope this phase.** `--archetype` is the only new flag; the bare
  command is left as-is and its reshape is deferred.

## Open

- **CLI shape.** Whether the bare command is reshaped to the grouped catalog
  view. Deferred, per the "CLI is disposable" ordering — revisit after the
  NOOA run.
- **Validation.** The pre-build trigger is met (see *Status* — the discovery
  stall is observed in NOOA traces). The post-build check is a NOOA run
  (future-directions §3): does the agent (a) classify to the right class via
  `browse`, (b) retrieve the right card, (c) call it conventionally, offline —
  and does the two-stage affordance cut the stall rate versus the current
  single-stage `--ask` flow? Misses there are the trigger list for any
  further change (e.g. the `domain` field).
