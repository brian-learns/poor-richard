"""One-time data fetch for the financedatabase card.

financedatabase 2.x reads bz2 CSVs; the default mode downloads them from
GitHub on every instantiation (no good for an offline almanack). With
use_local_location=True it reads a fixed local directory:
<site-packages>/compression/<FILE_NAME>.

Run once (needs network):

    uv run python scripts/fetch_financedatabase.py

After that the golden test runs fully offline (and skips if the data is
absent, e.g. on a fresh machine).
"""

import sys
from pathlib import Path
from urllib.request import urlretrieve

REPO = "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
FILES = [
    "equities.bz2",
    "etfs.bz2",
    "funds.bz2",
    "indices.bz2",
    "currencies.bz2",
    "cryptos.bz2",
    "moneymarkets.bz2",
]


def target_dir() -> Path:
    import financedatabase

    return Path(financedatabase.__file__).resolve().parent.parent / "compression"


def main() -> int:
    dest = target_dir()
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        path = dest / name
        if path.exists() and path.stat().st_size > 0:
            print(f"  {name}: already present ({path.stat().st_size / 1e6:.2f} MB)")
            continue
        url = REPO + name
        print(f"  {name}: downloading {url}")
        urlretrieve(url, path)
        print(f"  {name}: {path.stat().st_size / 1e6:.2f} MB -> {path}")
    print(f"done. data dir: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
