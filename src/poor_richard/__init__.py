"""Poor Richard - a modern almanack of offline reference libraries."""

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


def main() -> int:
    """Print the reference-card registry."""
    verified = sum(1 for c in CARDS for q in c.questions if q.status == "verified")
    try:
        print(f"{'id':<20} {'pypi':<22} {'archetypes':<28} {'offline':<15} license")
        for card in CARDS:
            arch = ",".join(a.value for a in card.archetypes) or "-"
            status = "verified" if card.offline_verified else "not verified"
            print(f"{card.id:<20} {card.pypi:<22} {arch:<28} {status:<15} {card.license}")
        print(f"\n{len(CARDS)} reference cards; {verified} verified golden questions")
    except BrokenPipeError:
        # piped output, e.g. `poor-richard | head`; keep shutdown quiet
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
