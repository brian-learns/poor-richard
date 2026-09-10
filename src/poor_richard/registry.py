"""Machine-readable reference cards for the Poor Richard almanack.

Each :class:`ReferenceCard` describes one library: the question archetypes it
answers, where its data comes from, how it stays offline, its footprint and
license, and its golden questions.

Golden questions with ``status="verified"`` must have a passing test in
``tests/test_golden.py``; ``tests/test_registry.py`` enforces that linkage and
keeps the cards in sync with ``pyproject.toml``. See ``docs/reference-cards.md``
for the full design and the golden-question test method.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "Archetype",
    "UpdateModel",
    "Question",
    "ReferenceCard",
    "CARDS",
    "get",
    "by_pypi",
    "search",
]


class Archetype(str, Enum):
    """The shape of the question a reference library answers."""

    LOOKUP = "lookup"
    CONVERT = "convert"
    COMPUTE = "compute"
    VALIDATE = "validate"
    TEMPORAL = "temporal"
    PARSE = "parse"
    GENERATE = "generate"


class UpdateModel(str, Enum):
    """How a library's data stays current."""

    STATIC = "static"
    SNAPSHOT = "per-release snapshot"
    ALGORITHMIC = "algorithmic"


@dataclass(frozen=True)
class Question:
    """A golden question: what an agent might ask, and the known-correct answer."""

    question: str
    expected: str
    status: str = "candidate"  # "candidate" | "verified"
    test_id: str | None = None  # test function in tests/test_golden.py


@dataclass(frozen=True)
class ReferenceCard:
    id: str  # stable slug
    name: str
    pypi: str  # PyPI distribution name
    import_name: str  # top-level module
    archetypes: tuple[Archetype, ...]
    provenance: str
    update_model: UpdateModel
    offline: bool  # works with no network
    offline_verified: bool  # golden tests passed with sockets blocked
    footprint: str
    native_deps: str
    license: str
    questions: tuple[Question, ...]
    notes: str = ""
    example: str = ""  # curated snippet; empty => derive from the golden test
    keywords: str = ""  # curated search tokens (issue #2); folded into _card_text


_A = Archetype
_U = UpdateModel

CARDS: tuple[ReferenceCard, ...] = (
    # ------------------------------------------------------------------ geo
    ReferenceCard(
        id="pycountry",
        name="pycountry",
        pypi="pycountry",
        import_name="pycountry",
        archetypes=(_A.LOOKUP,),
        provenance="ISO 3166-1/2/3, 639-3, 4217, 15924 official lists + CLDR translations",
        keywords="country numeric subdivision former code",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="23 MB",
        native_deps="none",
        license="LGPL-2.1",
        questions=(
            Question("ISO 3166-1 alpha-3 for France?", "FRA", "verified", "test_pycountry"),
            Question("ISO 4217 name for JPY?", "Yen", "verified", "test_pycountry"),
            Question("ISO 639-1 'de' language name?", "German", "verified", "test_pycountry"),
        ),
    ),
    ReferenceCard(
        id="python-iso639",
        name="python-iso639",
        pypi="python-iso639",
        import_name="iso639",
        archetypes=(_A.LOOKUP, _A.CONVERT),
        provenance="ISO 639-1/2/3 (SIL International registry)",
        keywords="three letter macrolanguage bibliographic terminological",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="432 KB",
        native_deps="none",
        license="Apache-2.0",
        questions=(
            Question("ISO 639-3 code for ISO 639-1 'de'?", "deu (639-2/B is 'ger')", "verified", "test_iso639"),
        ),
        notes="ALL_LANGUAGES is a set of Language(part1, part2b, part2t, part3, name); "
        "there is no Lang() constructor.",
    ),
    ReferenceCard(
        id="babel",
        name="Babel",
        pypi="babel",
        import_name="babel",
        archetypes=(_A.LOOKUP, _A.CONVERT),
        provenance="CLDR (Unicode Common Locale Data Repository): display names, plural rules, "
        "number/currency/date formats per locale",
        keywords="translation i18n l10n percent timezone",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="33 MB installed (~10 MB wheel; 32 MB is bundled CLDR locale data)",
        native_deps="none",
        license="BSD-3-Clause",
        questions=(
            Question("English display name for locale 'de'?", "German", "verified", "test_babel"),
            Question("Russian plural categories for 2, 5, 21?", "few, many, one (CLDR ru rules)", "verified", "test_babel"),
            Question("Format 1234.5 in en_US?", "1,234.5", "verified", "test_babel"),
            Question("Format 1234.50 USD in de_DE?", "1.234,50 $ (U+00A0 no-break space before the symbol)", "verified", "test_babel"),
            Question("Full date for 2026-02-05 in 'en'?", "Thursday, February 5, 2026", "verified", "test_babel"),
        ),
        notes="2.18: plural evaluation is Locale('ru').plural_form(n) - a property "
        "returning a callable PluralRule; the old plural_rule() method and "
        "babel.plural.to_plural import are gone. get_display_name() returns None "
        "for most region-specific locales (fr_FR, de_DE, ja_JP): CLDR's "
        "localeDisplayNames covers only a subset (script variants and BCP-47 "
        "extensions); use the base locale ('de') for language names. Number and "
        "currency output may embed U+00A0 no-break spaces (de_DE currency: "
        "'1.234,50 $').",
    ),
    ReferenceCard(
        id="countryinfo",
        name="countryinfo",
        pypi="countryinfo",
        import_name="countryinfo",
        archetypes=(_A.LOOKUP,),
        provenance="maintainer-curated (Wikipedia-derived); lower authority than ISO",
        keywords="population timezone coordinates flag tld",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="2 MB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Capital of Japan?", "Tokyo", "verified", "test_countryinfo"),
        ),
        notes="Class is CountryInfo (capital-I); name()/capital() are methods, not attributes.",
    ),
    ReferenceCard(
        id="timezonefinder",
        name="timezonefinder",
        pypi="timezonefinder",
        import_name="timezonefinder",
        archetypes=(_A.CONVERT,),
        provenance="Natural Earth timezone shapefiles, memory-mapped",
        keywords="local utc offset coordinates gps",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="372 KB + 63 MB timezonefinder-data package",
        native_deps="none (mmap)",
        license="MIT",
        questions=(
            Question("IANA zone for (48.8566, 2.3522)?", "Europe/Paris", "verified", "test_timezonefinder"),
        ),
        notes="timezone_at() takes keyword-only lng/lat (not lon).",
    ),
    ReferenceCard(
        id="postal",
        name="postal (libpostal bindings)",
        pypi="pypostal-multiarch",
        import_name="postal",
        archetypes=(_A.PARSE, _A.CONVERT),
        provenance="libpostal C library (OpenStreetPostcodes + curated global data)",
        keywords="address zip street geocode duplicate",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="916 KB",
        native_deps="libpostal.so.1 (system library)",
        license="MIT",
        questions=(
            Question(
                "Parse '1600 Pennsylvania Avenue NW, Washington, DC 20500' (US)?",
                "house_number=1600, road=pennsylvania avenue nw, city=washington, state=dc, postcode=20500",
                "verified",
                "test_postal",
            ),
        ),
        notes="PyPI name collision x3: 'postal' (text dedupe lib) and 'pypostal' "
        "(mail-sending client) are unrelated. pypostal-multiarch is the OpenVenues "
        "binding rebundled with multi-arch wheels; it needs system libpostal.so.1 on "
        "the loader path (tests preload it via ctypes, skipping if absent).",
        example=(
            "from postal.parser import parse_address\n"
            "from postal.expand import expand_address\n"
            "\n"
            "r = {t: v for v, t in parse_address(\n"
            "    '1600 Pennsylvania Avenue NW, Washington, DC 20500', country='united states')}\n"
            "# golden: r['house_number'] == '1600' and r['postcode'] == '20500'\n"
            "alts = expand_address('1600 Penn Ave NW')  # 'northwest' -> 'NW' & co.\n"
        ),
    ),
    ReferenceCard(
        id="h3",
        name="h3",
        pypi="h3",
        import_name="h3",
        archetypes=(_A.CONVERT,),
        provenance="Uber H3 v4 spec; hexagonal geospatial indexing (C reference implementation)",
        keywords="geohash hexagon hexbin spatial geocoding",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="1 MB wheel (3.2 MB installed, C extension)",
        native_deps="none (bundled C extension)",
        license="Apache-2.0",
        questions=(
            Question("H3 cell at res 2 for (20, 123)?", "824b9ffffffffff", "verified", "test_h3"),
            Question("Center of H3 cell 8928342e20fffff?", "(37.5012466151, -122.5003039349)", "verified", "test_h3"),
            Question("Base cell of 85283473fffffff?", "20", "verified", "test_h3"),
            Question("Grid distance 85283473fffffff -> 8528342bfffffff?", "2", "verified", "test_h3"),
        ),
        notes="H3 v4 cell IDs are incompatible with v3: old-docs indices like "
        "0x89283082809fff3 raise H3CellInvalidError. v4 Python API is flat "
        "(latlng_to_cell/cell_to_latlng; the old geo_to_h3 names are gone); "
        "cells accept hex strings and latlng_to_cell takes (lat, lng, res). "
        "Spec regression vectors ship in the h3 repo's tests/cli/. "
        "Also a transitive dep of timezonefinder.",
    ),
    # ------------------------------------------------------- physics/units
    ReferenceCard(
        id="scipy.constants",
        name="scipy.constants",
        pypi="scipy",
        import_name="scipy",
        archetypes=(_A.LOOKUP,),
        provenance="NIST CODATA recommended values",
        keywords="planck boltzmann avogadro faraday rydberg",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="96 MB (full SciPy)",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Speed of light in vacuum, m/s?", "299792458 (exact by definition)", "verified", "test_scipy_constants"),
        ),
    ),
    ReferenceCard(
        id="astropy.constants",
        name="astropy.constants",
        pypi="astropy",
        import_name="astropy",
        archetypes=(_A.LOOKUP,),
        provenance="CODATA + IAU; values carry explicit uncertainty and unit metadata",
        keywords="parsec astronomical solar mass hubble",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="42 MB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Gravitational constant G?", "6.67430(15)e-11 m^3 kg^-1 s^-2 (CODATA 2018)", "verified", "test_astropy_constants"),
        ),
        notes="astropy's built-in ephemeris (get_body, default 'builtin') is offline; "
        "used here as a cross-check oracle for ephem.",
    ),
    ReferenceCard(
        id="pint",
        name="pint",
        pypi="pint",
        import_name="pint",
        archetypes=(_A.CONVERT, _A.COMPUTE),
        provenance="curated unit registry (SI, NIST, historical, information units)",
        keywords="temperature celsius fahrenheit kelvin degree unit conversion",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="1.4 MB",
        native_deps="none",
        license="BSD",
        questions=(
            Question("1 kWh in joules?", "3.6e6 J", "verified", "test_pint"),
        ),
    ),
    ReferenceCard(
        id="chemformula",
        name="chemformula",
        pypi="chemformula",
        import_name="chemformula",
        archetypes=(_A.PARSE, _A.COMPUTE),
        provenance="periodic-table data (IUPAC weights)",
        keywords="molecular water glucose caffeine sulfuric",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="68 KB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Composition and formula weight of H2SO4?", "H:2 S:1 O:4, 98.072 g/mol", "verified", "test_chemformula"),
        ),
        notes="v1.x: class is ChemFormula; formula_weight and element are properties "
        "(not methods); no molar_mass/elements attributes.",
    ),
    ReferenceCard(
        id="periodictable",
        name="periodictable",
        pypi="periodictable",
        import_name="periodictable",
        archetypes=(_A.LOOKUP,),
        provenance="IUPAC / CIAAW atomic weights, isotope data",
        keywords="iron hydrogen gold copper density",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="2.6 MB",
        native_deps="none",
        license="Public domain",
        questions=(
            Question("Fe atomic number and mass?", "26 / 55.845", "verified", "test_periodictable"),
        ),
        notes="v2.x: elements are top-level (pt.Fe); attrs are number, mass, lowercase name.",
    ),
    ReferenceCard(
        id="uncertainties",
        name="uncertainties",
        pypi="uncertainties",
        import_name="uncertainties",
        archetypes=(_A.COMPUTE,),
        provenance="algorithmic - implements GUM (Guide to the Expression of Uncertainty in Measurement)",
        keywords="propagation sigma correlation covariance deviation",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="308 KB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("(2.0 +/- 0.1) * (3.0 +/- 0.1)?", "6.0 +/- 0.3606 (independent errors)", "verified", "test_uncertainties"),
        ),
    ),
    ReferenceCard(
        id="ambiance",
        name="ambiance",
        pypi="ambiance",
        import_name="ambiance",
        archetypes=(_A.LOOKUP, _A.COMPUTE),
        provenance="ICAO Doc 7488-3 / ISO 2533 International Standard Atmosphere 1993 (7 layers, -5 to 80 km)",
        keywords="altitude lapse mach flight level",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="76 KB (numpy/scipy already in tree)",
        native_deps="none (pure Python on numpy/scipy)",
        license="Apache-2.0",
        questions=(
            Question("ISA sea-level temperature?", "288.15 K (15 degC, exact by definition)", "verified", "test_ambiance"),
            Question("ISA sea-level pressure and density?", "101325 Pa, 1.225 kg/m3 (exact by definition)", "verified", "test_ambiance"),
            Question("ISA speed of sound at sea level?", "340.29 m/s (sqrt(1.4 * R * T0))", "verified", "test_ambiance"),
            Question("ISA temperature at the tropopause (22632 Pa)?", "216.65 K (11019 m geometric = 11 km geopotential)", "verified", "test_ambiance"),
        ),
        notes="Atmosphere(h) takes GEOMETRIC height; internally it converts to "
        "geopotential (H = h(1 - h/R)), so the ISA table values (e.g. 22632 Pa / "
        "216.65 K at 11 km) are reached at 11019 m geometric, not 11000 m. "
        "Properties return numpy arrays - index with [0] for scalar input. "
        "from_pressure()/from_density() invert via scipy.optimize. Valid range "
        "-5004 to 81020 m (raises ValueError outside).",
    ),
    # -------------------------------------------------------- temporal/fin
    ReferenceCard(
        id="holidays",
        name="holidays",
        pypi="holidays",
        import_name="holidays",
        archetypes=(_A.TEMPORAL,),
        provenance="maintainer-encoded holiday rules per country/subdivision",
        keywords="christmas thanksgiving easter diwali observed",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="8.2 MB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Is 2025-07-04 a US holiday?", "True (Independence Day)", "verified", "test_holidays"),
        ),
    ),
    ReferenceCard(
        id="python-dateutil",
        name="python-dateutil",
        pypi="python-dateutil",
        import_name="dateutil",
        archetypes=(_A.PARSE, _A.TEMPORAL),
        provenance="RFC-style parsers; relativedelta arithmetic",
        keywords="rrule recurrence 5545 fuzzy timezone",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="752 KB",
        native_deps="none",
        license="Apache-2.0 / BSD (dual)",
        questions=(
            Question("Parse '20250615T093000Z'?", "2025-06-15 09:30:00+00:00", "verified", "test_dateutil"),
        ),
    ),
    ReferenceCard(
        id="workalendar",
        name="workalendar",
        pypi="workalendar",
        import_name="workalendar",
        archetypes=(_A.TEMPORAL,),
        provenance="maintainer-curated business calendars (built on holidays)",
        keywords="france french germany bank weekend",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="1.4 MB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Next US working day after 2025-12-25?", "2025-12-26", "verified", "test_workalendar"),
        ),
        notes="v17: US calendar moved to workalendar.usa; use instance methods "
        "is_working_day()/add_working_days() (next_workday is gone).",
    ),
    ReferenceCard(
        id="convertdate",
        name="convertdate",
        pypi="convertdate",
        import_name="convertdate",
        archetypes=(_A.CONVERT, _A.TEMPORAL,),
        provenance="Standard calendar algorithms: Julian Day arithmetic, Maimonides' Hebrew intercalation, "
        "tabular Islamic 30-year cycle, French Republican Year I epoch, Mayan GMT correlation constant 584283",
        keywords="hijri nowruz tzolkin persian haab",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="400 KB (pulls in pymeeus, already in the tree)",
        native_deps="none",
        license="MIT",
        questions=(
            Question("What is 2000-02-28 in the Julian calendar?", "2000-02-15 (13 days behind, 1900–2100)", "verified", "test_convertdate"),
            Question("Hebrew date for 2024-10-03?", "1 Tishrei 5785 (first day of Rosh Hashanah)", "verified", "test_convertdate"),
            Question("Islamic date for 622-07-19 (Gregorian)?", "1 Muharram 1 AH (Hijra epoch)", "verified", "test_convertdate"),
            Question("French Republican date for 1792-09-22?", "1 Brumaire Year I", "verified", "test_convertdate"),
            Question("Mayan Long Count for 2012-12-21?", "13.0.0.0.0 (end of the 13th b'ak'tun; GMT correlation)", "verified", "test_convertdate"),
        ),
        notes="2.x API: each module exposes from_gregorian(y,m,d)/to_gregorian(...) via Julian Day "
        "(1.x's gregorian_to_<cal> functions are gone) and 1.x's chinese module was removed. "
        "islamic is the tabular (arithmetic) calendar, not moon-sighting. "
        "french_republican.MONTHS[0] is 'Vendémiaire' but month 1 is Brumaire — "
        "the tuple's first two entries are swapped; don't use it for month names. "
        "Already a transitive dependency of workalendar.",
    ),
    ReferenceCard(
        id="iso4217",
        name="iso4217",
        pypi="iso4217",
        import_name="iso4217",
        archetypes=(_A.LOOKUP,),
        provenance="ISO 4217 currency list (names, minor-unit decimals)",
        keywords="euro yen pound numeric gold",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="68 KB",
        native_deps="none",
        license="Public domain",
        questions=(
            Question("Minor-unit decimals for JPY?", "0", "verified", "test_iso4217"),
            Question("ISO 4217 name for USD?", "US Dollar", "verified", "test_iso4217"),
        ),
        notes="Data is in raw_table[code] dict (CcyNm, CcyNbr, CcyMnrUnts); the "
        "Currency enum maps lowercase code -> uppercase code string.",
    ),
    ReferenceCard(
        id="python-stdnum",
        name="python-stdnum",
        pypi="python-stdnum",
        import_name="stdnum",
        archetypes=(_A.VALIDATE,),
        provenance="ISO/IEC 7812-1 (Luhn), ISO 13616 (IBAN), ISO 21047 (ISBN), GS1 (EAN/UPC), plus VIN, national IDs",
        keywords="credit card luhn ean upc vin checksum",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="4.3 MB",
        native_deps="none",
        license="LGPL",
        questions=(
            Question("Is IBAN DE89370400440532013000 valid?", "yes (spec example)", "verified", "test_stdnum"),
            Question("Does 4111111111111111 pass Luhn?", "yes", "verified", "test_stdnum"),
            Question("Is ISBN-13 9783161484100 valid?", "yes", "verified", "test_stdnum"),
        ),
        notes="v2.x: iban.validate() raises ValidationError on bad checksum; "
        "luhn.is_valid()/isbn.is_valid(); old is_valid_iban/isValid names are gone.",
    ),
    ReferenceCard(
        id="phonenumbers",
        name="phonenumbers",
        pypi="phonenumbers",
        import_name="phonenumbers",
        archetypes=(_A.PARSE, _A.VALIDATE),
        provenance="Phone number parsing/validation/formatting per the ITU E.164 numbering plan (Google libphonenumber data)",
        keywords="e164 calling code landline mobile",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="24 MB (bundled metadata)",
        native_deps="none",
        license="Apache-2.0",
        questions=(
            Question("Parse +493012345678 (DE)?", "country_code=49, region=DE, type=FIXED_LINE", "verified", "test_phonenumbers"),
        ),
    ),
    # --------------------------------------------------------- formats/io
    ReferenceCard(
        id="python-magic",
        name="python-magic",
        pypi="python-magic",
        import_name="magic",
        archetypes=(_A.PARSE,),
        provenance="libmagic database (from file(1), community-maintained)",
        keywords="type binary extension octet gzip",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="32 KB",
        native_deps="libmagic (system)",
        license="MIT",
        questions=(
            Question("MIME of a minimal valid PNG?", "image/png", "verified", "test_python_magic"),
        ),
        notes="Short header stubs may not match on minimal system libmagic builds; "
        "use complete file headers in golden questions.",
    ),
    ReferenceCard(
        id="filetype",
        name="filetype",
        pypi="filetype",
        import_name="filetype",
        archetypes=(_A.PARSE,),
        provenance="community-curated magic bytes (pure-Python alternative to libmagic)",
        keywords="jpg pdf webp heic mp3",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="252 KB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Format of 89 50 4E 47 0D 0A 1A 0A ...?", "image/png", "verified", "test_filetype"),
        ),
    ),
    ReferenceCard(
        id="tldextract",
        name="tldextract",
        pypi="tldextract",
        import_name="tldextract",
        archetypes=(_A.PARSE,),
        provenance="Mozilla Public Suffix List",
        keywords="tld subdomain hostname registrable url",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="452 KB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Public suffix of www.example.co.uk?", "co.uk", "verified", "test_tldextract"),
        ),
        notes="Use TLDExtract(suffix_list_urls=()) to force the bundled snapshot; "
        "the default constructor may fetch an update on first use.",
    ),
    ReferenceCard(
        id="user-agents",
        name="user-agents",
        pypi="user-agents",
        import_name="user_agents",
        archetypes=(_A.PARSE,),
        provenance="Mozilla UA-parser definitions",
        keywords="browser chrome bot android windows",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="40 KB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Parse an iPhone Safari 17 user-agent string?", "device=iPhone, os=iOS", "verified", "test_user_agents"),
        ),
    ),
    ReferenceCard(
        id="email-validator",
        name="email-validator",
        pypi="email-validator",
        import_name="email_validator",
        archetypes=(_A.VALIDATE, _A.PARSE,),
        provenance="RFC 5322 address syntax grammar (with RFC 6531/6532 SMTPUTF8 support); "
        "domain handling per RFC 1123 dot-atom + IDNA2008 via the idna library",
        keywords="rfc5322 quoted atext displayname mailbox",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="1.5 MB (96 KB code + 1.4 MB dnspython, new dep)",
        native_deps="none",
        license="Unlicense (public domain)",
        questions=(
            Question("Is postmaster@example.com a valid RFC 5322 address?", "yes", "verified", "test_email_validator"),
            Question("Is user.name+tag@example.com valid?", "yes (+ is a valid atext)", "verified", "test_email_validator"),
            Question("Is user@exam_ple.com valid?", "no (underscore not allowed in domain labels)", "verified", "test_email_validator"),
            Question("Is @example.com valid?", "no (empty local part)", "verified", "test_email_validator"),
            Question("Normalize First.Local@Example.COM?", "First.Local@example.com (domain lowercased, local case kept)", "verified", "test_email_validator"),
            Question("Domain of user@xn--r8jz45g.jp?", "例え.jp (IDNA2008-decoded)", "verified", "test_email_validator"),
        ),
        notes="check_deliverability=False is the offline path; True performs live "
        "MX lookups via dnspython (DNS = network, blocked in the test suite). "
        "2.x: there is no normalize_email() - use validate_email(...).normalized. "
        "Normalization lowercases the domain but keeps local-part case (RFC 5321); "
        ".normalized / .domain decode the domain from punycode to Unicode "
        "(user@xn--r8jz45g.jp -> domain '例え.jp'). Underscores in the domain are "
        "rejected (RFC 5322 dot-atom, unlike RFC 1123 hostnames).",
    ),
    # ----------------------------------------------------------- astronomy
    ReferenceCard(
        id="skyfield",
        name="skyfield",
        pypi="skyfield",
        import_name="skyfield",
        archetypes=(_A.COMPUTE, _A.TEMPORAL),
        provenance="NASA JPL DE ephemerides (de421/de405); timescale data bundled",
        keywords="moon phase position rise distance",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="1.2 MB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("TT Julian date at the J2000.0 epoch?", "2451545.0007429 (TT-UTC = 64.184 s)", "verified", "test_skyfield"),
        ),
        notes="v1.55: ts.utc(y, m, d, h) is numeric (string parsing broken); Time has "
        "no .jd attr - use .tt/.tai/.tdb floats. Planetary ephemerides must be "
        "downloaded (ephem.bsp no longer bundled).",
    ),
    ReferenceCard(
        id="ephem",
        name="ephem",
        pypi="ephem",
        import_name="ephem",
        archetypes=(_A.COMPUTE,),
        provenance="XEphem C library (VSOP87 planetary theory)",
        keywords="mars jupiter transit ecliptic moonset",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="small C extension",
        native_deps="C extension",
        license="LGPL",
        questions=(
            Question("Julian date anchor: float(Date('2000/1/1 12:00:00')) + 2415020.0?", "2451545.0 (J2000, exact)", "verified", "test_ephem_j2000_anchor"),
            Question("Moon phase angle 2025-06-15 12:00 UTC?", "~228.8 deg (waning gibbous; pymeeus 228.8, astropy 228.2)", "candidate", "test_ephem_moon_phase"),
        ),
        notes="KNOWN BUG (2026-09): the 4.2.1 wheel returns wrong moon positions and "
        "an internally inconsistent phase (82.9 deg) on this platform; astropy and "
        "pymeeus agree on ~228.8 deg. The phase test is an xfail canary. "
        "float(Date) = JD - 2415020.0 (1900-01-01 12:00 UT). pyephem 9.99 on PyPI "
        "is an empty shim that depends on ephem.",
    ),
    ReferenceCard(
        id="sgp4",
        name="sgp4",
        pypi="sgp4",
        import_name="sgp4",
        archetypes=(_A.COMPUTE,),
        provenance="Spacetrack-standard SGP4/SDP4 implementation",
        keywords="satellite orbit position propagation norad",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="704 KB",
        native_deps="C extension",
        license="MIT",
        questions=(
            Question("ISS (TLE 25544, 2008) altitude at TLE epoch?", "342 km (within 300-450 km LEO band)", "verified", "test_sgp4"),
        ),
        notes="Satrec.twoline2rv(line1, line2) returns a Satrec directly (no error "
        "tuple); sgp4_tsince(tmin) -> (error, r, v) in km, TEME frame.",
    ),
    ReferenceCard(
        id="astral",
        name="astral",
        pypi="astral",
        import_name="astral",
        archetypes=(_A.COMPUTE, _A.TEMPORAL),
        provenance="Meeus, Astronomical Algorithms",
        keywords="sunrise sunset twilight day length",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="244 KB",
        native_deps="none",
        license="Apache-2.0",
        questions=(
            Question("Sunrise in New York (40.7128, -74.0060) on 2025-06-21?", "09:25 UTC (~05:25 EDT, June solstice)", "verified", "test_astral"),
        ),
        notes="v3.x: Observer(latitude, longitude) + astral.sun.sunrise(observer, date); "
        "the v2 Sun class is gone.",
    ),
    ReferenceCard(
        id="pymeeus",
        name="pymeeus (PyMeeus)",
        pypi="pymeeus",
        import_name="pymeeus",
        archetypes=(_A.COMPUTE, _A.TEMPORAL),
        provenance="Meeus, Astronomical Algorithms (2nd ed.): abridged VSOP87 solar theory, ELP2000 lunar theory",
        keywords="obliquity nutation aberration precession libration",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="3.0 MB (sdist only, no wheel)",
        native_deps="none",
        license="LGPL-3.0",
        questions=(
            Question("Sun apparent ecliptic longitude 2025-06-15 12:00 UTC?", "84.641 deg (just under the 90 deg solstice; agrees with pysweph to 0.001 deg)", "verified", "test_pymeeus"),
            Question("Moon geocentric ecliptic position 2025-06-15 12:00 UTC?", "lon 313.464 deg, lat -3.157 deg (elongation 228.8 deg - the ephem canary's value)", "verified", "test_pymeeus"),
            Question("2025 spring equinox (UTC)?", "2025-03-20 09:01:28 (published 09:01:54 UTC)", "verified", "test_pymeeus"),
            Question("Julian date of the J2000.0 epoch?", "2451545.0 (2000-01-01 12:00 TT, exact by definition)", "verified", "test_pymeeus"),
        ),
        notes="Module and class share names: `from pymeeus import Sun` gives the MODULE; "
        "the class is `pymeeus.Sun.Sun` (same for Moon), and Epoch is "
        "`from pymeeus.Epoch import Epoch`. Angles convert with float() (no .deg()); "
        "Sun.apparent_geocentric_position -> (lon, lat, r_au); "
        "Moon.geocentric_ecliptical_pos -> (lon, lat, dist_km, parallax). "
        "Epoch defaults to TT; for UTC input use utc=True (internal leap table "
        "frozen at 2017: TAI-UTC = 37 s, still correct until the next leap "
        "second). sdist-only package, last release 2022. The 228.8 deg moon "
        "elongation is the independent oracle behind the ephem xfail canary.",
    ),
    # ---------------------------------------------------------------- color
    ReferenceCard(
        id="colour-science",
        name="colour-science",
        pypi="colour-science",
        import_name="colour",
        archetypes=(_A.CONVERT, _A.COMPUTE),
        provenance="CIE standards (CIE 1931/1964, CIELAB, CAM16, ...)",
        keywords="rgb hsl oklab p3 delta",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="95 MB installed (76 MB is a bundled htmlcov artifact; real code ~19 MB)",
        native_deps="none (needs networkx for the conversion graph)",
        license="BSD-3",
        questions=(
            Question("sRGB pure red -> CIE Lab?", "(53.23, 80.09, 67.20)", "verified", "test_colour"),
        ),
        notes="The real package is 'colour-science' on PyPI; an unrelated toy package "
        "owns the name 'colour'. convert() graph node is 'CIE Lab' and returns "
        "scale-1 values (L in [0, 1]).",
    ),
    # ----------------------------------------------------------------- bio
    ReferenceCard(
        id="biopython",
        name="biopython",
        pypi="biopython",
        import_name="Bio",
        archetypes=(_A.LOOKUP, _A.COMPUTE),
        provenance="IUPAC / IUBMB nomenclature, standard genetic code, codon tables",
        keywords="ecori bamhi fasta genbank gc",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="17 MB (Bio package)",
        native_deps="none",
        license="BSD-3 (Biopython license)",
        questions=(
            Question("Codon ATG in the standard code?", "M (methionine); TAA is a stop", "verified", "test_biopython"),
        ),
        notes="1.8x: codon tables expose forward_table dict and stop_codons set; "
        "seq1() maps stop codons to X - use Seq.translate() for real translation.",
    ),
    # -------------------------------------------------------------- hybrid
    ReferenceCard(
        id="starfile",
        name="starfile",
        pypi="starfile",
        import_name="starfile",
        archetypes=(_A.PARSE,),
        provenance="MRC Group STAR (STar Relational) format (structural biology / cryo-EM)",
        keywords="relion micrograph defocus ctf tomogram",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="40 KB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Parse a .star file with a 2-row pixel array?", "columns pixel.x/pixel.y/pixel.intensity, values round-trip", "verified", "test_starfile"),
        ),
        notes="read() returns a DataBlock (pandas DataFrame); column names drop the "
        "leading underscore.",
        example=(
            "import starfile\n"
            "from pathlib import Path\n"
            "\n"
            "star = (\n"
            "    'data_block\\n\\n'\n"
            "    'loop_\\n'\n"
            "    '_pixel.x\\n_pixel.y\\n_pixel.intensity\\n'\n"
            "    '1.0 2.0 100.0\\n'\n"
            "    '3.0 4.0 200.0\\n'\n"
            ")\n"
            "p = Path('example.star')\n"
            "p.write_text(star)\n"
            "blk = starfile.read(p)\n"
            "# golden: list(blk.columns) == ['pixel.x', 'pixel.y', 'pixel.intensity']\n"
            "# golden: blk['pixel.x'].tolist() == [1.0, 3.0]\n"
        ),
    ),
    ReferenceCard(
        id="czml3",
        name="czml3",
        pypi="czml3",
        import_name="czml3",
        archetypes=(_A.GENERATE,),
        provenance="Cesium CZML specification",
        keywords="trajectory geospatial wgs84 3d time",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="small (pydantic models)",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Generate a CZML packet with one position sample?", "{'id': ..., 'position': {'epoch': ..., 'cartesian': [x, y, z]}}", "verified", "test_czml3"),
        ),
        notes="3.x is pydantic-based: czml3.Packet(id=..., position=czml3.properties.Position(...)); "
        "serialize with model_dump(by_alias=True, exclude_none=True).",
    ),
    # ------------------------------------------------------- candidate tier
    ReferenceCard(
        id="isodate",
        name="isodate",
        pypi="isodate",
        import_name="isodate",
        archetypes=(_A.PARSE,),
        provenance="ISO 8601 date/time/duration grammar",
        keywords="ordinal week offset aware period",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="160 KB",
        native_deps="none",
        license="BSD",
        questions=(
            Question("Parse ISO 8601 duration 'P1Y2M3DT4H5M6S'?", "1y 2m 3d 4h 5m 6s", "verified", "test_isodate"),
        ),
    ),
    ReferenceCard(
        id="mimeparse",
        name="mimeparse",
        pypi="mimeparse",
        import_name="mimeparse",
        archetypes=(_A.PARSE,),
        provenance="RFC 2045 media-range grammar",
        keywords="content accept multipart boundary q",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="32 KB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Parse 'text/html; charset=utf-8'?", "(text, html, {charset: utf-8})", "verified", "test_mimeparse"),
        ),
        notes="Abandoned (last release 2013): best_match() is broken on py3 "
        "(dict.has_key); parse_mime_type/parse_media_range work fine.",
    ),
    ReferenceCard(
        id="molmass",
        name="molmass",
        pypi="molmass",
        import_name="molmass",
        archetypes=(_A.COMPUTE,),
        provenance="IUPAC atomic weights",
        keywords="dalton molecular glucose caffeine ethanol",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="288 KB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Molar mass of H2O?", "18.015 g/mol", "verified", "test_molmass"),
        ),
        notes="2026.x API: top-level `molmass` is a module, not callable; "
        "use `molmass.Formula('H2O').mass`.",
    ),
    ReferenceCard(
        id="mido",
        name="mido",
        pypi="mido",
        import_name="mido",
        archetypes=(_A.PARSE,),
        provenance="Standard MIDI File (SMF) format",
        keywords="tempo bpm pitch program sysex",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="416 KB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Round-trip a note_on(60)/note_off(60) MIDI file?", "messages preserved on reload", "verified", "test_mido"),
        ),
        notes="save() takes a filename, not a file object; filter MetaMessage "
        "(isinstance) when iterating tracks.",
        example=(
            "import mido\n"
            "\n"
            "mid = mido.MidiFile()\n"
            "track = mido.MidiTrack()\n"
            "mid.tracks.append(track)\n"
            "track.append(mido.Message('note_on', note=60, velocity=64, time=0))\n"
            "track.append(mido.Message('note_off', note=60, velocity=64, time=480))\n"
            "mid.save('example.mid')  # save() takes a filename, not a file object\n"
            "readback = mido.MidiFile('example.mid')\n"
            "notes = [m for m in readback.tracks[0] if isinstance(m, mido.Message)]\n"
            "# golden: [(m.type, m.note, m.velocity) for m in notes] == [('note_on', 60, 64), ('note_off', 60, 64)]\n"
        ),
    ),
    ReferenceCard(
        id="particle",
        name="particle",
        pypi="particle",
        import_name="particle",
        archetypes=(_A.LOOKUP,),
        provenance="PDG (Particle Data Group) extended particle data + MC identification codes (GEANT3, Corsika-7, Pythia)",
        keywords="proton neutron electron muon evtgen",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="1.7 MB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("Particle with PDG code 13?", "mu-, mass 105.6583755 MeV", "verified", "test_particle"),
        ),
        notes="Particle.from_pdgid(code) is the lookup path; mass is in MeV.",
    ),
    ReferenceCard(
        id="geographiclib",
        name="geographiclib",
        pypi="geographiclib",
        import_name="geographiclib",
        archetypes=(_A.COMPUTE,),
        provenance="Karney's geodesy algorithms, WGS84 ellipsoid",
        keywords="bearing azimuth route midpoint destination",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="260 KB",
        native_deps="C extension",
        license="MIT",
        questions=(
            Question("Great-circle distance Paris -> London?", "343.9 km", "verified", "test_geographiclib"),
        ),
        notes="Geodesic.WGS84 is a ready-made instance (not a factory); "
        "Inverse() returns a dict - s12 is the distance in metres.",
    ),
    ReferenceCard(
        id="bizdays",
        name="bizdays",
        pypi="bizdays",
        import_name="bizdays",
        archetypes=(_A.TEMPORAL,),
        provenance="bundled exchange holiday calendars + bridge to pandas_market_calendars",
        keywords="NYSE XNYS exchange business day trading",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="116 KB",
        native_deps="none",
        license="BSD",
        questions=(
            Question("Next XNYS business day after 2025-12-25?", "2025-12-26", "verified", "test_bizdays"),
        ),
        notes="Calendar.load('PMC/XNYS') bridges to pandas_market_calendars; "
        "next-business-day is adjust_next()/adjust_previous().",
    ),
    ReferenceCard(
        id="charset-normalizer",
        name="charset-normalizer",
        pypi="charset-normalizer",
        import_name="charset_normalizer",
        archetypes=(_A.PARSE,),
        provenance="statistical heuristics (no data)",
        keywords="mojibake garbled codepage latin1 utf8",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="1.1 MB",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Encoding of a UTF-8 accented string?", "utf_8", "verified", "test_charset_normalizer"),
        ),
        notes="UTF-8/ASCII detection is robust; the single-byte cp125x family is "
        "ambiguous for short samples (may return cp1250/cp1257 for cp1252 text).",
    ),
    ReferenceCard(
        id="idna",
        name="idna",
        pypi="idna",
        import_name="idna",
        archetypes=(_A.CONVERT,),
        provenance="RFC 5890 IDNA2008 (UAX #58 + RFC 3490/3491/3492/5891/5892)",
        keywords="punycode idn unicode ascii nfkc",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="428 KB",
        native_deps="none",
        license="BSD-3",
        questions=(
            Question("IDNA-encode the domain 例え.jp?", "xn--r8jz45g.jp", "verified", "test_idna"),
        ),
    ),
    ReferenceCard(
        id="pandas-market-calendars",
        name="pandas-market-calendars",
        pypi="pandas-market-calendars",
        import_name="pandas_market_calendars",
        archetypes=(_A.TEMPORAL,),
        provenance="per-market curated exchange calendars (sessions, holidays, half days)",
        keywords="nasdaq lse tsx thanksgiving juneteenth",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="1.1 MB (pandas already in tree)",
        native_deps="none",
        license="MIT",
        questions=(
            Question("XNYS valid sessions 2025-12-24..31?", "24, 26, 29, 30, 31 (no Christmas, no weekends)", "verified", "test_pandas_market_calendars"),
        ),
        notes="4.6.1: valid_days(start, end) is the session API; holidays() "
        "returns an offset object in this version. Pins pandas < 3.",
    ),
    ReferenceCard(
        id="financedatabase",
        name="financedatabase",
        pypi="financedatabase",
        import_name="financedatabase",
        archetypes=(_A.LOOKUP,),
        provenance="Curated classification of 305k financial symbols (112k equities, 36k ETFs, 58k funds, 91k indices, currencies, cryptos) with sector/industry/exchange/ISIN",
        keywords="ticker stock index cusip bitcoin",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="100 KB code + ~20 MB bz2 CSV data (one-time fetch)",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Sector of AAPL?", "Information Technology", "verified", "test_financedatabase"),
            Question("Base/quote of EURUSD=X?", "EUR / USD", "verified", "test_financedatabase"),
        ),
        notes="Default mode re-downloads CSVs from GitHub per instantiation; "
        "use use_local_location=True after `uv run python "
        "scripts/fetch_financedatabase.py` (data -> <site-packages>/compression/). "
        "Symbol is the DataFrame index, not a column: use .data.loc['AAPL']. "
        "search() with no match returns the ENTIRE table (do not print it). "
        "Heavy transitive deps (scikit-learn, yfinance) via financetoolkit.",
        example=(
            "from financedatabase import Equities, Currencies\n"
            "\n"
            "# data must be fetched once: uv run python scripts/fetch_financedatabase.py\n"
            "eq = Equities(use_local_location=True)\n"
            "aapl = eq.data.loc['AAPL']  # symbol is the index, not a column\n"
            "# golden: aapl['sector'] == 'Information Technology'\n"
            "cur = Currencies(use_local_location=True)\n"
            "pair = cur.data.loc['EURUSD=X']\n"
            "# golden: (pair['base_currency'], pair['quote_currency']) == ('EUR', 'USD')\n"
        ),
    ),
    ReferenceCard(
        id="chemicals",
        name="chemicals",
        pypi="chemicals",
        import_name="chemicals",
        archetypes=(_A.LOOKUP,),
        provenance="ChEDL: curated pure-component property data cross-referenced across literature sources",
        keywords="antoine acentric critical boiling vapor",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="73 MB (bundled property data)",
        native_deps="none",
        license="MIT",
        questions=(
            Question("Molecular weight of water (CAS 7732-18-5)?", "18.0153 g/mol", "verified", "test_chemicals"),
        ),
        notes="Key by CAS-RN (MW('7732-18-5')). Part of Caleb Bell's ChEDL; "
        "thermo/fluids build the computation layer on top (not installed).",
    ),
    ReferenceCard(
        id="pysweph",
        name="pysweph",
        pypi="pysweph",
        import_name="swisseph",
        archetypes=(_A.COMPUTE,),
        provenance="AstroDienst Swiss Ephemeris 2.10 (community fork of pyswisseph)",
        keywords="moon houses ascendant position zodiac",
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="2 MB (single compiled .so, Moshier ephemeris built in)",
        native_deps="none (self-contained extension module)",
        license="AGPL-2.0",
        questions=(
            Question(
                "Sun ecliptic longitude 2025-06-15 12:00 UTC?",
                "84.641 deg (JD 2460842.0, just under the 90 deg solstice)",
                "verified",
                "test_pysweph",
            ),
        ),
        notes="NOT backwards-compatible with pyswisseph: calc_ut returns "
        "(results, retflags, warning_str), flags are FLG_* (FLG_SWIEPH|FLG_SPEED "
        "default), results is a 6-tuple with speeds. Without the .se1/.se2 data "
        "files it falls back to the built-in Moshier ephemeris (arcsecond-class, "
        "cross-checked vs astropy/JPL; check the returned warning string). "
        "AGPL-2.0 — accepted for this project on maintainer decision.",
    ),
    # ---------------------------------------------------------- auxiliaries
    ReferenceCard(
        id="networkx",
        name="networkx (auxiliary)",
        pypi="networkx",
        import_name="networkx",
        archetypes=(),
        provenance="enabler: colour-science's shortest-path colour-conversion graph",
        keywords="node edge dijkstra pagerank centrality",
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="13 MB",
        native_deps="none",
        license="BSD-3",
        questions=(),  # auxiliary: exercised through the colour-science card
        example=(
            "import networkx as nx\n"
            "\n"
            "g = nx.Graph()\n"
            "g.add_edges_from([(\"sRGB\", \"CIEXYZ\"), (\"CIEXYZ\", \"sRGB\"), (\"CIEXYZ\", \"HSV\")])\n"
            "# golden: nx.has_path(g, \"sRGB\", \"HSV\") is True\n"
        ),
    ),
)


def get(card_id: str) -> ReferenceCard:
    """Look up a card by its stable id."""
    for card in CARDS:
        if card.id == card_id:
            return card
    raise KeyError(f"unknown card id: {card_id!r}")


def by_pypi(pypi_name: str) -> ReferenceCard:
    """Look up a card by its PyPI distribution name."""
    for card in CARDS:
        if card.pypi == pypi_name:
            return card
    raise KeyError(f"unknown pypi distribution: {pypi_name!r}")


# ------------------------------------------------------------------ search
#
# Fuzzy lookup over the cards: question text, provenance, notes, and
# name-like fields. The corpus is a few KB, so a stdlib linear scan is
# the right tool - no index, no extra dependency, fully offline.

_STOP = frozenset(
    "a an and at be by can do does for from how in is it its of on or "
    "the to what which with".split()
)
_TOKEN = re.compile(r"\w+")
_MIN_SCORE = 0.25


def _tokens(text: str) -> set[str]:
    out = set()
    for t in _TOKEN.findall(text.lower()):
        if t in _STOP:
            continue
        # naive plural fold: "numbers" -> "number" (not "ss": "business")
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.add(t)
    return out


def _card_text(card: ReferenceCard) -> str:
    parts = [card.name, card.pypi, card.import_name, card.provenance, card.keywords, card.notes]
    parts += [f"{q.question} {q.expected}" for q in card.questions]
    return " ".join(parts)


def search(query: str, top: int = 3) -> list[tuple[float, ReferenceCard, Question | None]]:
    """Rank cards against a natural-language query.

    Returns up to `top` (score, card, matched_question) triples, best
    first. Score is query-token coverage of the card text plus a
    difflib name-similarity bonus (so `color` finds `colour-science`).
    Empty list when nothing clears the threshold.
    """
    qt = _tokens(query)
    if not qt:
        return []
    results: list[tuple[float, ReferenceCard, Question | None]] = []
    for card in CARDS:
        coverage = len(qt & _tokens(_card_text(card))) / len(qt)
        names = (card.id, card.name, card.pypi, card.import_name)
        name_sim = max(
            (difflib.SequenceMatcher(None, a, b).ratio() for a in (query, *qt) for b in names),
            default=0.0,
        )
        score = coverage + 0.5 * name_sim
        if score < _MIN_SCORE:
            continue
        best_q = max(
            (q for q in card.questions if _tokens(q.question) & qt),
            key=lambda q: len(_tokens(q.question) & qt),
            default=None,
        )
        results.append((round(score, 3), card, best_q))
    results.sort(key=lambda r: -r[0])  # stable: card order breaks ties
    return results[:top]
