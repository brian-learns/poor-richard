"""Poor Richard - a modern almanack of offline reference libraries."""

import importlib
import os
import sys

from poor_richard.registry import (
    CARDS,
    Archetype,
    Question,
    ReferenceCard,
    UpdateModel,
    by_pypi,
    get,
)

__all__ = [
    "CARDS",
    "Archetype",
    "Question",
    "ReferenceCard",
    "UpdateModel",
    "by_pypi",
    "get",
    "main",
]

USAGE = "usage: poor-richard [--help <module>]"


def main(argv: list[str] | None = None) -> int:
    """Print the reference-card registry, or help() for one module."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] in (["--help"], ["-h"]):
            return _show_help(argv[1:])
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
