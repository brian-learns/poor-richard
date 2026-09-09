# Task: enhance one ReferenceCard with curated search keywords

You have been assigned a single library **import name** (given in your prompt,
e.g. `stdnum`). Your job: examine that library, then add **5 high-value
keywords** to its card so that natural-language queries route to it.

**You may only edit `./src/poor_richard/registry.py`.** Do not touch tests,
docs, other cards, or anything else. All 43 carded libraries are already
installed in `./.venv` — do not install anything. Work offline.

## How search works (so you can judge keyword value)

`poor_richard.search(query)` scores each card by query-token coverage of the
card text (name, pypi, import name, provenance, `keywords`, notes, and golden
questions) plus a `difflib` name-similarity bonus. A keyword is only worth
adding if it flips a real, misrouted query — not if it just sounds relevant.
See issue #2 (this repo) for the measurements behind this approach.

## Steps

1. **Find your card.** In `src/poor_richard/registry.py`, locate the
   `ReferenceCard` whose `import_name` equals your assigned name. The import
   name often differs from the id/pypi (e.g. `stdnum` ↔ `python-stdnum`,
   `colour` ↔ `colour-science`). If no card matches your assigned name, stop
   and report that — do not guess.

2. **Read the existing card text.** Note the `provenance`, `notes`, and
   `questions` — keywords must be tokens **absent** from that text (repeating
   existing tokens is worthless). If the card already has a `keywords`
   field, you were told the four curated ones (`pint`, `python-stdnum`,
   `astral`, `bizdays`) came from measurements: only change one if you can
   clearly do better; otherwise verify and report "no change".

3. **Examine the library.** Import it and play with it in `.venv/bin/python`:
   the module docstring, public members, and — most importantly — the
   **standards, units, and identifiers in its data**. High-value terms live in
   the domain data (e.g. `celsius` in pint's unit registry, `luhn` in
   stdnum's validators), not in API names or docstrings.

4. **Find the routing gaps.** Draft 8–12 natural questions an agent or human
   would ask that *should* land on your card (the style of the card's golden
   questions helps). Run them through search and see which misroute:

   ```bash
   .venv/bin/python - <<'EOF'
   from poor_richard import search
   queries = [
       "celsius to fahrenheit conversion",
       "check a credit card number with luhn",
       # ... your candidates
   ]
   for q in queries:
       r = search(q, top=1)
       print(f"{q!r:45} -> {r[0][1].id if r else 'none'}")
   EOF
   ```

   Tokens missing from your card text in the misrouted queries are your
   keyword candidates.

5. **Pick exactly 5 tokens.** Quality bar, in order:
   - A person would actually type it: standard names/numbers, unit names,
     identifier types (iban, isbn, vin, ean), colloquial domain words
     (sunrise, checksum, solstice).
   - Not already in your card's existing text (step 2).
   - **Distinctive across all 43 cards** — grep `registry.py` for the token;
     if it strongly belongs to another card, it will cause collisions, not
     fixes (never put `credit card` on anything but `python-stdnum`).
   - Not generic filler: `data`, `convert`, `number`, `date`, `library`,
     `validate`, `calculation` are useless on their own.
   - Lowercase, singular (search folds plurals), space-separated.

6. **Make the edit.** One line, placed directly after the card's
   `provenance=` line, matching the existing style (see the `pint` card):

   ```python
       provenance="...",
       keywords="temperature celsius fahrenheit kelvin degree unit conversion",
   ```

7. **Verify (required before you finish):**
   - Re-run your probes: each keyword's representative query should now rank
     your card top-1 (or clearly higher than before).
   - Run the full suite: `.venv/bin/python -m pytest -q` (~10 s). Any failure
     caused by your change must be fixed or the keyword reverted — in
     particular the regression fixtures in
     `src/poor_richard/tests/test_registry.py` (`test_search_keywords` and
     friends) protect the already-curated cards.

## Report

End with a short final message (the only thing the operator reads):

```
card: <id> (<import_name>)
keywords: <the 5 tokens>
probes: <n>/<n> now rank top-1  (list any that still misroute, with the winner)
tests: 60 passed, 1 xfailed
```

If you made no change (already curated, or nothing better found), say so in
one line with the reason.
