## 🗺️ Geographic, Country & Political Registries

* [pycountry](https://github.com/pycountry/pycountry): The gold standard offline database for political registries. It contains full mappings for ISO country codes (3166), languages (639-3), currencies (4217), and administrative subdivisions.
* [iso639](https://github.com/jacksonllee/iso639): A lightweight package dedicated strictly to language code normalization, mapping between ISO 639-1, 639-2, and 639-3 variants effortlessly. `uv add python-iso639`
* [countryinfo](https://github.com/porimol/countryinfo): An offline database providing granular geographic and cultural metadata about countries, including capitals, bordering nations, timezones, provinces, and official languages.
* [timezonefinder](https://github.com/jannikmi/timezonefinder): A highly efficient offline lookup library that utilizes memory-mapped coordinate boundaries to translate raw latitude and longitude coordinates directly into standard IANA timezone names (e.g., America/Los_Angeles).
* [pypostal-multiarch](https://pypi.org/project/pypostal-multiarch/) (bindings to [libpostal](https://github.com/openvenues/libpostal)): A blazing-fast binding to libpostal (C), providing complete offline parse and normalization capabilities for global street addresses into structured components across different languages. `uv add pypostal-multiarch` — note: the PyPI names `postal` and `pypostal` belong to unrelated packages, and the C extension needs the system `libpostal.so.1`.

## 🔬 Physics, Scientific Constants & Measurement Units

* scipy.[constants](https://docs.scipy.org/doc/scipy/reference/constants.html#module-scipy.constants): The most lightweight way to expose authoritative physical constants if you already have SciPy in your stack. It provides everything from atomic masses and electromagnetic values to basic mathematical anchors.
* astropy.[constants](https://astro-docs.readthedocs.io/en/latest/constants/): Exposes fundamental physical and astronomical constants wrapped in explicit metadata containers containing their standard system units, naming variations, and rigorous uncertainty/error bounds.
* [pint](https://github.com/hgrecco/pint): A comprehensive unit-manipulation and conversion engine. It includes a massive built-in registry of physical, computational, and historical measurement units, allowing an agent to perform exact conversions mathematically without hallucinating equations.
* [chemformula](https://github.com/molshape/ChemFormula): A specialized, lightweight parser designed to take raw text strings of chemical formulas and output structural weight, composition breakdowns, and parsed elemental frequencies without querying the web.

## 📅 Temporal, Calendar & Financial Standards

* [holidays](https://github.com/vacanza/holidays/): A fast, offline library that dynamically computes local, national, and religious bank holidays across hundreds of countries and administrative subdivisions on the fly for any calendar year.
* [dateutil](https://github.com/dateutil/dateutil): A powerful extension to the standard datetime module. It features a complete relativedelta engine capable of computing exact semantic relative ranges (e.g., "the next third Tuesday of the month"). `uv add python-dateutil`
* [workalendar](https://github.com/workalendar/workalendar): A heavy-duty calendar extension that handles complex structural corporate schedules, computing working days, shipping deadlines, and regional labor holidays globally.
* [iso4217](https://github.com/dahlia/iso4217): A minimal, fast registry package dedicated strictly to mapping national currency codes to their precise legal names and decimal point configurations.

## 🏷️ Technical Formats, Encodings & Media Triage

* magic / python-magic: An offline wrapper around libmagic that inspects byte arrays or file headers directly to return authoritative MIME-type definitions, ensuring the agent correctly identifies binary files independent of their extensions.
* user-agents: An extraction engine that parses raw browser user-agent strings locally to output clear, structured attributes identifying device types, operating systems, and browser families.

## 🔭 Astronomy, Celestial Mechanics & Ephemerides

* skyfield: The modern gold standard for high-precision celestial math in Python. It calculates positions for the planets, stars, and Earth satellites directly from official NASA JPL ephemerides (de421 or de405 data files). It can accurately calculate local rising/setting times, lunar phases, and orbital coordinates entirely offline.
* astropy: A massive, institutional-grade library for astronomy. For reference data, its submodules are invaluable:
   * astropy.coordinates: Built-in datasets for all major celestial coordinate systems (ICRS, Galactic, AltAz).
   * astropy.time: Reference transformations between scale systems (UTC, TAI, Julian Dates).
* ephem / pyephem: A legacy but incredibly fast, lightweight library built on the classic XEphem C-library. It tracks planetary positions, constellations, and moon phases with an incredibly small memory footprint, making it ideal for smaller local models to parse.
* sgp4: The definitive low-level library for tracking Earth satellites. If your agent is passed a standard TLE (Two-Line Element) set from a document, sgp4 computes the satellite's exact latitude, longitude, and altitude relative to Earth at any second without hitting the internet.

## 占 Astrology & Horoscopic Mechanics

* flatlib: A Python engine specifically designed for traditional, western, and horoscopic astrology calculations. It abstracts low-level celestial positions into astrological concepts, returning exact houses, planetary aspects, zodiacal positions, and traditional essential dignities natively.
* kerykeion: A modern, object-oriented framework for astrology built directly on top of the Swiss Ephemeris (pyswisseph). It effortlessly structures data into clean Pydantic-like models, outputting full natal charts, aspects, and planetary positions as clean dictionary schemas that models like Qwen or Spark can read instantly.
* pyswisseph: The official Python binding to the Swiss Ephemeris, which is the undisputed, highly optimized C-library used by almost all professional astrology software worldwide. It provides maximum precision for planetary positions, house systems (Placidus, Koch, Regiomontanus), and lunar nodes spanning a 10,000-year window entirely locally.

## 🧩 Hybrid & Miscellaneous Star References

* starfile: A specialized, fast parser for .star (STar Relational) files, heavily used in structural biology and electron microscopy data modeling for tracking geometric particle arrays.
* czml3: A library to generate metadata architectures in CZML format, allowing an agent to cleanly format dynamic 3D celestial or satellite tracking paths so they can be piped directly into 3D visualizers like Cesium.

