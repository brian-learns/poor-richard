"""Lazy, discoverable front-end to every reference library in the registry.

Importing this package is cheap: it loads only the registry's card data, not
any of the libraries. Accessing an attribute (``pra.shapely``) imports that
one library on demand, and ``dir()`` / REPL tab-completion list them all.
"""
import importlib

from poor_richard.registry import CARDS

__all__ = sorted({c.import_name for c in CARDS})


def __getattr__(name: str):
    if name in __all__:
        return importlib.import_module(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
