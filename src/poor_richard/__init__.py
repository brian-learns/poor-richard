"""Poor Richard - a modern almanack of offline reference libraries."""

import ast
import importlib
import os
import sys
from pathlib import Path

from poor_richard.registry import (
    CARDS,
    Archetype,
    Question,
    ReferenceCard,
    UpdateModel,
    by_pypi,
    browse,
    catalog,
    get,
    search,
)

__all__ = [
    "CARDS",
    "Archetype",
    "Question",
    "ReferenceCard",
    "UpdateModel",
    "by_pypi",
    "browse",
    "catalog",
    "example",
    "get",
    "main",
    "search",
]

USAGE = "usage: poor-richard [--help <module> | --example [id ...] | --archetype <a[,b...]> | --ask <query>]"

# Golden tests ship inside the package so examples work from the wheel too.
_GOLDEN_TEST_FILE = Path(__file__).parent / "tests" / "test_golden.py"


def main(argv: list[str] | None = None) -> int:
    """Print the registry, help() for a module, usage examples, or a ranking."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] in (["--help"], ["-h"]):
            return _show_help(argv[1:])
        if argv[:1] == ["--example"]:
            return _print_examples(argv[1:])
        if argv[:1] == ["--archetype"]:
            return _browse(argv[1:])
        if argv[:1] == ["--ask"]:
            return _ask(argv[1:])
        return _print_cards()
    except BrokenPipeError:
        # piped output, e.g. `poor-richard | head`; keep shutdown quiet
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 1


def _print_cards() -> int:
    verified = sum(1 for c in CARDS for q in c.questions if q.status == "verified")
    print(f"{'id':<20} {'pypi':<22} {'archetypes':<28} {'offline':<15} license")
    for card in CARDS:
        arch = ",".join(a.value for a in card.archetypes) or "-"
        status = "verified" if card.offline_verified else "not verified"
        print(f"{card.id:<20} {card.pypi:<22} {arch:<28} {status:<15} {card.license}")
    print(f"\n{len(CARDS)} reference cards; {verified} verified golden questions")
    return 0


def _resolve_names(args: list[str]) -> tuple[list[ReferenceCard], set[str]]:
    """Match args against card ids / PyPI names / import names.

    Returns (matched_cards, unknown_names); empty args match all cards.
    """
    wanted = set(args)
    if not wanted:
        return list(CARDS), set()
    known = set()
    for card in CARDS:
        known.update((card.id, card.pypi, card.import_name))
    unknown = wanted - known
    matched = [c for c in CARDS if wanted & {c.id, c.pypi, c.import_name}]
    return matched, unknown


def _derive_example(test_id: str) -> str:
    """Re-emit a golden test as a usage example.

    Non-assert statements are re-parsed and re-emitted; asserts become
    `# golden:` comments so the verified values stay visible. Reads the
    test source file - never imports the libraries - so this is fast and
    works from an installed wheel.
    """
    try:
        tree = ast.parse(_GOLDEN_TEST_FILE.read_text())
    except (OSError, SyntaxError):
        return ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == test_id:
            lines = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assert):
                    lines.append(f"# golden: {ast.unparse(stmt.test)}")
                else:
                    lines.append(ast.unparse(stmt))
            return "\n".join(lines)
    return ""


def _example_body(card: ReferenceCard) -> str:
    if card.example:
        return card.example.rstrip("\n")
    test_id = next(
        (q.test_id for q in card.questions if q.status == "verified" and q.test_id),
        f"test_{card.id}",
    )
    return _derive_example(test_id)


def example(card_id: str) -> str:
    """Return the conventional usage snippet for a card (stage 2 of the flow).

    The card's curated snippet if it has one, otherwise the card's golden test
    re-emitted with its assertions as `# golden:` comments (so the verified
    values stay visible). Same source as `poor-richard --example <id>`.
    """
    return _example_body(get(card_id))


def _print_examples(args: list[str]) -> int:
    matched, unknown = _resolve_names(args)
    if unknown:
        for name in sorted(unknown):
            print(f"poor-richard: unknown card: {name!r}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    blocks = []
    for card in matched:
        body = _example_body(card)
        if not body:
            print(f"poor-richard: no example for {card.id!r}", file=sys.stderr)
            return 1
        header = f"# poor-richard: {card.name} (pypi: {card.pypi}, {card.license})"
        blocks.append(f"{header}\n# {card.provenance}\n{body}")
    print("\n\n".join(blocks))
    return 0


def _browse(args: list[str]) -> int:
    """Render the catalog filtered by one or more archetypes (stage 1)."""
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    names = [n.strip() for n in args[0].split(",") if n.strip()]
    archetypes: list[Archetype] = []
    for name in names:
        try:
            archetypes.append(Archetype(name))
        except ValueError:
            valid = ", ".join(a.value for a in Archetype)
            print(f"poor-richard: unknown archetype: {name!r} (choose from: {valid})", file=sys.stderr)
            return 2
    if not archetypes:
        print(USAGE, file=sys.stderr)
        return 2
    if len(archetypes) == 1:
        print(catalog(archetypes[0]))
    else:
        print("\n\n".join(catalog(a) for a in archetypes))
    return 0


def _ask(args: list[str]) -> int:
    """Rank cards against a natural-language query: '<score> <id>' per line."""
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    results = search(" ".join(args))
    if not results:
        print(f"poor-richard: no match for {' '.join(args)!r}", file=sys.stderr)
        return 1
    for score, card, _question in results:
        print(f"{score:.2f} {card.id}")
    return 0


def _show_help(args: list[str]) -> int:
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    name = args[0]
    # resolve card id or PyPI name to the import name; fall back to the raw name
    import_name = name
    for lookup in (get, by_pypi):
        try:
            import_name = lookup(name).import_name
            break
        except KeyError:
            pass
    try:
        module = importlib.import_module(import_name)
    except ImportError as exc:
        print(f"poor-richard: cannot import {import_name!r}: {exc}", file=sys.stderr)
        return 1
    help(module)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
