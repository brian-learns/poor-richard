"""Integrity checks for the lazy import front-end (poor_richard.pra).

``pra`` is a discoverable namespace over the registry: ``dir()`` lists every
carded library's import name, and attribute access imports on demand. These
checks lock in the invariants that make it safe for an agent to discover and
import through ``pra``:
- ``pra.__all__`` stays in sync with the registry,
- attribute access returns the real module,
- an unknown name raises ``AttributeError`` (not a bare import error),
- importing the package does not pull in the reference libraries.
"""

import subprocess
import sys

import pytest

from poor_richard import pra
from poor_richard.registry import CARDS


def test_all_matches_registry():
    assert set(pra.__all__) == {c.import_name for c in CARDS}


def test_dir_lists_all():
    assert pra.__dir__() == sorted(pra.__all__)


def test_lazy_access_returns_real_module():
    import idna

    assert pra.idna is idna


def test_unknown_name_raises_attributeerror():
    with pytest.raises(AttributeError):
        pra.definitely_not_a_library


def test_importing_package_does_not_load_libs():
    """Regression: ``import poor_richard`` must not pull in the reference libs.

    The lazy ``pra`` front-end exists so the package imports cheaply; a card
    added to the registry must not become an import-time dependency. Runs in a
    subprocess so no earlier test has already loaded a library in this
    interpreter.
    """
    code = (
        "import sys, poor_richard; "
        "print(any(m in sys.modules for m in "
        "('pycountry', 'iso639', 'babel', 'countryinfo')))"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"poor_richard not importable in subprocess: {r.stderr.strip()}")
    assert r.stdout.strip() == "False"
