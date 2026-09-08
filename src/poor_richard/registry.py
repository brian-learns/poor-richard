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
        update_model=_U.SNAPSHOT,
        offline=True,
        offline_verified=True,
        footprint="23 MB",
        native_deps="none",
        license="LGPL-2.1",
        questions=(
            Question("ISO 3166-1 alpha-3 for France?", "France", "verified", "test_pycountry"),
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
        id="countryinfo",
        name="countryinfo",
        pypi="countryinfo",
        import_name="countryinfo",
        archetypes=(_A.LOOKUP,),
        provenance="maintainer-curated (Wikipedia-derived); lower authority than ISO",
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
    ),
    # ------------------------------------------------------- physics/units
    ReferenceCard(
        id="scipy.constants",
        name="scipy.constants",
        pypi="scipy",
        import_name="scipy",
        archetypes=(_A.LOOKUP,),
        provenance="NIST CODATA recommended values",
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
    # -------------------------------------------------------- temporal/fin
    ReferenceCard(
        id="holidays",
        name="holidays",
        pypi="holidays",
        import_name="holidays",
        archetypes=(_A.TEMPORAL,),
        provenance="maintainer-encoded holiday rules per country/subdivision",
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
        id="iso4217",
        name="iso4217",
        pypi="iso4217",
        import_name="iso4217",
        archetypes=(_A.LOOKUP,),
        provenance="ISO 4217 currency list (names, minor-unit decimals)",
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
        provenance="ITU E.164 numbering plan (Google libphonenumber data)",
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
    # ----------------------------------------------------------- astronomy
    ReferenceCard(
        id="skyfield",
        name="skyfield",
        pypi="skyfield",
        import_name="skyfield",
        archetypes=(_A.COMPUTE, _A.TEMPORAL),
        provenance="NASA JPL DE ephemerides (de421/de405); timescale data bundled",
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
    # ---------------------------------------------------------------- color
    ReferenceCard(
        id="colour-science",
        name="colour-science",
        pypi="colour-science",
        import_name="colour",
        archetypes=(_A.CONVERT, _A.COMPUTE),
        provenance="CIE standards (CIE 1931/1964, CIELAB, CAM16, ...)",
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
    ),
    ReferenceCard(
        id="czml3",
        name="czml3",
        pypi="czml3",
        import_name="czml3",
        archetypes=(_A.GENERATE,),
        provenance="Cesium CZML specification",
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
    ),
    ReferenceCard(
        id="particle",
        name="particle",
        pypi="particle",
        import_name="particle",
        archetypes=(_A.LOOKUP,),
        provenance="PDG (Particle Data Group) extended particle data + MC identification codes (GEANT3, Corsika-7, Pythia)",
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
        id="chemicals",
        name="chemicals",
        pypi="chemicals",
        import_name="chemicals",
        archetypes=(_A.LOOKUP,),
        provenance="ChEDL: curated pure-component property data cross-referenced across literature sources",
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
        update_model=_U.ALGORITHMIC,
        offline=True,
        offline_verified=True,
        footprint="13 MB",
        native_deps="none",
        license="BSD-3",
        questions=(),  # auxiliary: exercised through the colour-science card
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
