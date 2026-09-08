# Reference library research list

Candidate libraries surveyed for Poor Richard. The machine-readable registry is
the single source of truth for what is installed and verified: see
`docs/reference-cards.md` (card table) and `uv run poor-richard`. Everything
listed below is installed unless marked *(candidate — not installed)*.

## 🗺️ Geographic, Country & Political Registries

* [pycountry](https://github.com/pycountry/pycountry): The gold standard offline database for political registries. It contains full mappings for ISO country codes (3166), languages (639-3), currencies (4217), and administrative subdivisions.
* [iso639](https://github.com/jacksonllee/iso639): A lightweight package dedicated strictly to language code normalization, mapping between ISO 639-1, 639-2, and 639-3 variants effortlessly. `uv add python-iso639`
* [countryinfo](https://github.com/porimol/countryinfo): An offline database providing granular geographic and cultural metadata about countries, including capitals, bordering nations, timezones, provinces, and official languages.
* [timezonefinder](https://github.com/jannikmi/timezonefinder): A highly efficient offline lookup library that utilizes memory-mapped coordinate boundaries to translate raw latitude and longitude coordinates directly into standard IANA timezone names (e.g., America/Los_Angeles).
* [pypostal-multiarch](https://pypi.org/project/pypostal-multiarch/) (bindings to [libpostal](https://github.com/openvenues/libpostal)): A blazing-fast binding to libpostal (C), providing complete offline parse and normalization capabilities for global street addresses into structured components across different languages. `uv add pypostal-multiarch` — note: the PyPI names `postal` and `pypostal` belong to unrelated packages, and the C extension needs the system `libpostal.so.1`.
* [geographiclib](https://github.com/geographiclib/geographiclib-python): The reference implementation of the Karney geodesy algorithms — sub-millimetre WGS84 distances, bearings, and geodesic lines (`Geodesic.WGS84.Inverse(...)`). `uv add geographiclib`

## 🔬 Physics, Scientific Constants & Measurement Units

* scipy.[constants](https://docs.scipy.org/doc/scipy/reference/constants.html#module-scipy.constants): The most lightweight way to expose authoritative physical constants if you already have SciPy in your stack. It provides everything from atomic masses and electromagnetic values to basic mathematical anchors.
* astropy.[constants](https://astro-docs.readthedocs.io/en/latest/constants/): Exposes fundamental physical and astronomical constants wrapped in explicit metadata containers containing their standard system units, naming variations, and rigorous uncertainty/error bounds.
* [pint](https://github.com/hgrecco/pint): A comprehensive unit-manipulation and conversion engine. It includes a massive built-in registry of physical, computational, and historical measurement units, allowing an agent to perform exact conversions mathematically without hallucinating equations.
* [chemformula](https://github.com/molshape/ChemFormula): A specialized, lightweight parser designed to take raw text strings of chemical formulas and output structural weight, composition breakdowns, and parsed elemental frequencies without querying the web.
* [periodictable](https://github.com/python-periodictable/periodictable): Periodic-table data (elements, isotopes, molar masses, phases) as queryable objects, plus ASCII table rendering — pure data, no native deps. `uv add periodictable`
* [uncertainties](https://github.com/lmfit/uncertainties): First-order uncertainty propagation for measured values (`UFloat`), with proper error-bar formatting of results. `uv add uncertainties`
* [particle](https://github.com/scikit-hep/particle): PDG particle data (masses, charges, lifetimes, decays) as offline queryable tables — `Particle.from_pdgid(13)` → μ⁻ at 105.658 MeV. `uv add particle`
* [molmass](https://github.com/cgohlke/molmass): Tiny molar-mass calculator from formula strings (IUPAC atomic weights). 2026.x API: the top-level `molmass` name is a *module*, not the old callable — use `molmass.Formula('H2O').mass`. `uv add molmass`
* [chemicals](https://github.com/CalebBell/chemicals): The largest pure-Python chemical-property database (CAS registry, critical constants, engineering correlations) that backs the ChEDL `thermo`/`fluids` stack — 73 MB of data, no native deps. `uv add chemicals`
* [colour-science](https://github.com/colour-science/colour): Colourimetry reference implementation (CIE colour spaces, chromatic adaptation, colour conversions). Note: the PyPI name is `colour-science` and it imports as `colour` — an unrelated toy package owns `colour` on PyPI. `uv add colour-science`

## 📅 Temporal, Calendar & Financial Standards

* [holidays](https://github.com/vacanza/holidays/): A fast, offline library that dynamically computes local, national, and religious bank holidays across hundreds of countries and administrative subdivisions on the fly for any calendar year.
* [dateutil](https://github.com/dateutil/dateutil): A powerful extension to the standard datetime module. It features a complete relativedelta engine capable of computing exact semantic relative ranges (e.g., "the next third Tuesday of the month"). `uv add python-dateutil`
* [workalendar](https://github.com/workalendar/workalendar): A heavy-duty calendar extension that handles complex structural corporate schedules, computing working days, shipping deadlines, and regional labor holidays globally.
* [iso4217](https://github.com/dahlia/iso4217): A minimal, fast registry package dedicated strictly to mapping national currency codes to their precise legal names and decimal point configurations.
* [isodate](https://github.com/gweis/isodate/): ISO 8601 date/time/duration parsing — `parse_duration('P1Y2M3DT4H5M6S')` yields `years`/`months`/`days` as ints and `seconds` as the total time seconds (14706). `uv add isodate`
* [bizdays](https://pypi.org/project/bizdays/): Business-day arithmetic over exchange calendars (bundles the `pandas_market_calendars` datasets as `PMC/XNYS` & co.) — `Calendar.load("PMC/XNYS").adjust_next(date)`. `uv add bizdays`
* [pandas-market-calendars](https://github.com/rsheftel/pandas_market_calendars): Exchange session calendars for pandas (open/close/auction times, valid sessions, holidays) — pins pandas 2.3.3. `uv add pandas-market-calendars`

## 🪪 Validation & Identifiers

* [python-stdnum](https://github.com/arthurdejong/python-stdnum): Validation and formatting for standard number systems (IBAN, ISIN, ISBN, VIN, CAS registry, & co.) — `uv add python-stdnum` (imports as `stdnum`; LGPL).
* [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers): Google's libphonenumber port — parses, validates, and formats phone numbers against the bundled E.164 country data. `uv add phonenumbers`

## 🏷️ Technical Formats, Encodings & Media Triage

* [python-magic](https://github.com/ahupp/python-magic): An offline wrapper around libmagic that inspects byte arrays or file headers directly to return authoritative MIME-type definitions, ensuring the agent correctly identifies binary files independent of their extensions.
* [user-agents](https://github.com/selwin/python-user-agents): An extraction engine that parses raw browser user-agent strings locally to output clear, structured attributes identifying device types, operating systems, and browser families.
* [filetype](https://github.com/h2non/filetype.py): Magic-byte file-type sniffing with no libmagic dependency — `filetype.guess(open(path, 'rb').read(1024))`. `uv add filetype`
* [tldextract](https://github.com/john-kurkowski/tldextract): Authoritative top-level-domain extraction from the bundled Public Suffix List snapshot — note: the first call may hit the network; pass `suffix_list_urls=()` to force the bundled list. `uv add tldextract`
* [charset-normalizer](https://github.com/Ousret/charset_normalizer): Text-encoding detection (the maintained successor to `chardet`) — reliable for UTF-8/ASCII; Windows-125x-family results can be ambiguous. `uv add charset-normalizer`
* [idna](https://github.com/kjd/idna): The IDNA 2008 / punycode reference implementation (what stdlib `socket` uses) — `idna.encode('例え.jp')` → `xn--r8jz45g.jp`. `uv add idna`
* [mimeparse](https://github.com/python/cpython/blob/main/Lib/mimeparse.py): RFC 2045 media-range parsing and matching. Abandoned (2013 release): `best_match()` is broken on py3 (`dict.has_key`), while `parse_mime_type`/`parse_media_range` work fine; the module now lives on in the CPython stdlib. `uv add mimeparse`
* [mido](https://github.com/mido/mido): Standard MIDI File reading and writing with typed `MetaMessage`/`Message` objects (filter `MetaMessage` when iterating tracks). `uv add mido`

## 🔭 Astronomy, Celestial Mechanics & Ephemerides

* [skyfield](https://github.com/skyfielders/skyfield): The modern gold standard for high-precision celestial math in Python. It calculates positions for the planets, stars, and Earth satellites directly from official NASA JPL ephemerides (de421 or de405 data files). It can accurately calculate local rising/setting times, lunar phases, and orbital coordinates entirely offline.
* [astropy](https://github.com/astropy/astropy): A massive, institutional-grade library for astronomy. For reference data, its submodules are invaluable:
   * astropy.coordinates: Built-in datasets for all major celestial coordinate systems (ICRS, Galactic, AltAz).
   * astropy.time: Reference transformations between scale systems (UTC, TAI, Julian Dates).
* [ephem](https://github.com/brandon-rhodes/pyephem) / pyephem: A legacy but incredibly fast, lightweight library built on the classic XEphem C-library. It tracks planetary positions, constellations, and moon phases with an incredibly small memory footprint, making it ideal for smaller local models to parse. Note: `pyephem` is an empty shim that just depends on `ephem` — depend on `ephem` directly. (Known bug: ephem 4.2.1 returns wrong moon positions on this platform; `test_ephem_moon_phase` is an xfail canary.)
* [sgp4](https://github.com/brandon-rhodes/python-sgp4): The definitive low-level library for tracking Earth satellites. If your agent is passed a standard TLE (Two-Line Element) set from a document, sgp4 computes the satellite's exact latitude, longitude, and altitude relative to Earth at any second without hitting the internet.
* [astral](https://github.com/sffjunkie/astral): Sunrise/sunset and moon-phase computation from an IANA timezone and solar position — no ephemeris files needed. `uv add astral`

## 占 Astrology & Horoscopic Mechanics

*(candidates — not installed; Swiss Ephemeris stack)*

* [flatlib](https://github.com/sinisa-markic/flatlib): A Python engine specifically designed for traditional, western, and horoscopic astrology calculations. It abstracts low-level celestial positions into astrological concepts, returning exact houses, planetary aspects, zodiacal positions, and traditional essential dignities natively.
* [kerykeion](https://github.com/robin900/Kerykeion): A modern, object-oriented framework for astrology built directly on top of the Swiss Ephemeris (pyswisseph). It effortlessly structures data into clean Pydantic-like models, outputting full natal charts, aspects, and planetary positions as clean dictionary schemas that models like Qwen or Spark can read instantly.
* [pyswisseph](https://pypi.org/project/pyswisseph/): The official Python binding to the Swiss Ephemeris, which is the undisputed, highly optimized C-library used by almost all professional astrology software worldwide. It provides maximum precision for planetary positions, house systems (Placidus, Koch, Regiomontanus), and lunar nodes spanning a 10,000-year window entirely locally.

## 🧩 Hybrid & Miscellaneous Star References

* [starfile](https://github.com/teamtomo/starfile): A specialized, fast parser for .star (STar Relational) files, heavily used in structural biology and electron microscopy data modeling for tracking geometric particle arrays.
* [czml3](https://github.com/Stoops-ML/czml3): A library to generate metadata architectures in CZML format, allowing an agent to cleanly format dynamic 3D celestial or satellite tracking paths so they can be piped directly into 3D visualizers like Cesium.
* [biopython](https://github.com/biopython/biopython/): The biology reference library — sequence I/O, taxonomy, genetics, and structure data, all bundled offline. `uv add biopython`
* [networkx](https://github.com/networkx/networkx) *(auxiliary)*: Graph data structures for cross-referencing (country adjacency, dependency graphs); a working tool rather than a reference source in itself. `uv add networkx`

## ⏳ Candidates not installed

Documented in `docs/reference-cards.md` §6 with reasons:

* [pyproj](https://github.com/pyproj/pyproj) — CRS/datum transforms (PROJ); heavier, native
* [rdkit](https://github.com/rdkit/rdkit) — SMILES/InChI, fingerprints; heavy native build
* [thermo](https://github.com/CalebBell/thermo) / [fluids](https://github.com/CalebBell/fluids) — ChEDL compute layer over `chemicals` (installed); not needed for lookup
* [pvlib](https://github.com/pvlib/pvlib-python) — solar position & irradiance (NREL SPA); native-ish
* [music21](https://github.com/music21/music21) — note names/scales/score analysis; large
* [rfc3987](https://pypi.org/project/rfc3987/) — IRI parsing; **GPL-3+**, excluded from default install (opt-in)
* [pysolar](https://pypi.org/project/pysolar/) — solar position; **GPL**, excluded from default install (opt-in)

> Hallucination note: `iana-registries` and `pybusday` from the original research
> list **do not exist on PyPI**. Business-day needs are covered by `bizdays` +
> `pandas-market-calendars` (both installed).
