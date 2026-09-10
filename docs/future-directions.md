# Future directions (tentative)

Proposals, not plans. Each item below was triggered by an observed gap, and is
written down so the tradeoffs are on record *before* anyone builds it. The
bar for promoting one of these to real work is a repeated, concrete miss —
not a hypothetical one.

## 1. A `keywords` field on cards (a.k.a. synonym table)

The concrete form this would take is a `keywords: tuple[str, ...]` field on
`ReferenceCard` — a curated shortlist of query vocabulary per card, living
next to the card in `registry.py` so it is reviewed and committed with the
card itself. Implementation is ~10 lines: `_card_text()` appends the keywords,
and keyword hits get a scoring weight above incidental mentions in `notes`
(so "water" on the molmass card beats "water" appearing once in some other
card's provenance). The golden queries would then be pinned in the existing
search tests: `search("water")[0] is molmass`, `search("solar times")[0] is
astral`, and so on. The mechanism is trivial; the actual cost is the
*curation* — someone has to enumerate, per card, the names an agent will
actually use: "H2O", "glucose" for molmass; "sessions", "trading days" for
the calendar cards; "sunrise", "dusk" for astral. That list never fully
converges, but each addition is one line, greppable, and testable. Note the
discipline established by the phonenumbers provenance fix: first try fixing
the card's own prose, and reach for keywords only where the card's natural
text cannot contain the query's vocabulary.

What a keyword field deliberately is *not* is a thesaurus or a semantic
layer. Enumerating every name for water combinatorially explodes, and more
fundamentally, some misses are conceptual rather than lexical — "how heavy is
glucose" fails because *heavy* means *molar mass*, which no finite keyword
list will ever contain. The honest boundary: keywords fix "right concept,
different words" (H2O/water, sessions/business days), and anything beyond
that is where the LLM sits — which is fine, because the almanack's job is to
be the *grounding* layer an agent queries, not to replace the agent's
language understanding. The field earns its place precisely because it is
small, explicit, and auditable rather than a fuzzy embedding index nobody can
inspect.

## 2. A built-in REPL

A minimum REPL would be a `--repl` (or `repl` subcommand) running a readline
loop that dispatches to the three existing modes: a line that parses as a
card id or PyPI name jumps straight to that card's example, anything else
goes through `search()` and prints the `<score> <id>` ranking, and follow-up
commands (`example`, `help`, `quit`) map 1:1 onto the current functions.
That is ~50 lines with zero new logic — a UI shell over `search()`,
`_example_body`, and `_show_help`, which means it cannot drift from the
one-shot CLI: both call the same code. The valuable additions would come on
top: tab-completion over card ids, and a `run` command that execs the derived
example in-process and shows its output, turning `ask` → `example` → `run`
into three keystrokes of exploration.

The honest counterweight: a REPL is a *browsing* tool for humans, and it is
strictly the wrong interface for the project's primary consumer, the LLM
agent, which prefers single invocations with clean stdout — `--ask` and
`poor_richard.search()` already are that, and a TTY loop is useless over a
pipe. It would also open a maintenance surface the project does not have
today (prompt handling, Ctrl-C semantics, non-TTY degradation) and set a
precedent for UX scope beyond the reference data. And per section 3, the
leading candidate agent harness already *is* a persistent Python REPL — so
if a REPL is ever built, it is for human browsing, and the keyword field
(section 1) should exist first, since its completion candidates are exactly
"card ids + keywords".

## 3. Notebook-style agent harnesses (test target: NOOA)

The leading framework we plan to test against is NVIDIA's Object-Oriented
Agents (NOOA, arXiv 2607.20709). Its CodeAct strategy gives the model
effectively a persistent, Jupyter-like Python session: the agent's action
space is just "call python" (execute a cell) and "return result"
(type-validated exit), and imports and local variables persist across cells
within a task. NOOA's stated design principle (P4) is to lean on the model's
existing Python knowledge — ordinary imports, popular libraries, no bespoke
DSL — and its context renderer surfaces the agent's docstrings and imported
libraries directly to the model.

What that means for Poor Richard, tentatively:

- **The Python API is the primary interface, the CLI is secondary.** In that
  environment the agent will `from poor_richard import search, get, CARDS`
  once and keep the session. `search("molar mass of water")` returning
  `(score, card, question)` triples is the shape that fits; the `--ask`/
  `--example` CLI modes are for humans. This is already how the API is
  designed, but it argues for keeping the Python surface clean and
  docstring-rich — in NOOA, docstrings are prompt material the model reads.
- **All carded libraries must be importable in the agent's environment.** The
  agent can `import molmass` directly; Poor Richard's added value there is
  *discovery* (which library answers this?), *verified answers* (the
  question/expected pairs), and *API-drift guardrails* (the card `notes` and
  derived examples record the API at the pinned version — molmass 2026.x's
  `Formula(...).mass`, pysweph's non-backwards-compatible `calc_ut` —
  exactly the failure mode of a model writing code from stale training
  knowledge).
- **Offline-first fits their sandboxing.** NOOA's hardened configurations
  run cells under seccomp network blocks; a library that fetches at import
  time or on first use (the `financedatabase` default mode) would simply not
  work there, while the almanack's socket-blocked test suite is the
  pre-existing proof that every card's golden path is network-free.

The natural first experiment, if pursued: install the wheel into a NOOA
CodeAct agent, give it factual tasks from the card questions ("what sector
is AAPL in?", "valid sessions on XNYS next week?"), and measure whether the
agent (a) discovers the right library via `search()`, (b) calls it
conventionally on the first attempt, and (c) answers correctly offline.
Misses from that run would be the trigger list for section 1.
