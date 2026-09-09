"""Golden questions for the Poor Richard reference libraries.

Each test answers one natural-language question with the API of a carded
library and asserts the independently known-correct value (from the standard
itself, not the package's docs). Test function names are the ``test_id``
referenced by the verified questions in ``poor_richard.registry.CARDS``;
``tests/test_registry.py`` enforces the linkage. Each golden test also pins
the registry's ``expected`` answer strings via ``_expected()`` in the same
test, so data drift in ``poor_richard/registry.py`` fails the suite.

All tests run with the network blocked (see tests/conftest.py).
"""

import math
import struct
import zlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from poor_richard.registry import get


def _expected(card: str, question: str) -> str:
    """The registry's golden answer for a card's question (data under test)."""
    for q in get(card).questions:
        if q.question == question:
            return q.expected
    raise AssertionError(f"{card}: unknown golden question {question!r}")


# --------------------------------------------------------------------- geo


def test_pycountry():
    import pycountry

    assert pycountry.countries.get(alpha_3="FRA").name == "France"
    assert pycountry.currencies.get(alpha_3="JPY").name == "Yen"
    assert pycountry.languages.get(alpha_2="de").name == "German"
    assert _expected("pycountry", "ISO 3166-1 alpha-3 for France?") == "FRA"
    assert _expected("pycountry", "ISO 4217 name for JPY?") == "Yen"
    assert _expected("pycountry", "ISO 639-1 'de' language name?") == "German"


def test_iso639():
    import iso639

    de = next(l for l in iso639.ALL_LANGUAGES if l.part1 == "de")
    assert de.part3 == "deu"  # ISO 639-3; 639-2/B is "ger"
    assert de.name == "German"
    assert _expected("python-iso639", "ISO 639-3 code for ISO 639-1 'de'?") == "deu (639-2/B is 'ger')"


def test_countryinfo():
    import countryinfo

    jp = countryinfo.CountryInfo("jp")
    assert jp.name() == "Japan"
    assert jp.capital() == "Tokyo"
    assert _expected("countryinfo", "Capital of Japan?") == "Tokyo"


def test_timezonefinder():
    from timezonefinder import TimezoneFinder

    tf = TimezoneFinder()
    assert tf.timezone_at(lng=2.3522, lat=48.8566) == "Europe/Paris"
    assert tf.timezone_at(lng=-74.0060, lat=40.7128) == "America/New_York"
    assert tf.timezone_at(lng=139.6917, lat=35.6895) == "Asia/Tokyo"
    assert _expected("timezonefinder", "IANA zone for (48.8566, 2.3522)?") == "Europe/Paris"


class LibpostalMissing(Exception):
    """Raised when the system libpostal.so.1 is not on disk."""


def _preload_libpostal():
    """libpostal.so.1 is a system library; preload it so the C extension binds."""
    import ctypes

    for candidate in (
        Path.home() / ".local/lib/libpostal.so.1",
        Path("/usr/local/lib/libpostal.so.1"),
        Path("/usr/lib/libpostal.so.1"),
    ):
        if candidate.exists():
            ctypes.CDLL(str(candidate))
            return
    raise LibpostalMissing


def test_postal():
    try:
        _preload_libpostal()
    except LibpostalMissing:
        pytest.skip("system libpostal.so.1 not found")
    from postal.parser import parse_address
    from postal.expand import expand_address

    # parse_address returns (value, type) pairs
    r = {
        t: v
        for v, t in parse_address(
            "1600 Pennsylvania Avenue NW, Washington, DC 20500",
            country="united states",
        )
    }
    assert r["house_number"] == "1600"
    assert r["road"] == "pennsylvania avenue nw"
    assert r["city"] == "washington"
    assert r["state"] == "dc"
    assert r["postcode"] == "20500"
    assert any("northwest" in alt for alt in expand_address("1600 Penn Ave NW"))
    assert _expected("postal", "Parse '1600 Pennsylvania Avenue NW, Washington, DC 20500' (US)?") == "house_number=1600, road=pennsylvania avenue nw, city=washington, state=dc, postcode=20500"

# ----------------------------------------------------------- physics/units


def test_scipy_constants():
    import scipy.constants as sc

    assert sc.c == 299792458.0  # exact by definition (SI)
    assert _expected("scipy.constants", "Speed of light in vacuum, m/s?") == "299792458 (exact by definition)"


def test_astropy_constants():
    from astropy import units as u
    from astropy.constants import G, c

    assert c.value == 299792458.0  # exact by definition (SI)
    # CODATA 2018: G = 6.67430(15) x 10^-11 m^3 kg^-1 s^-2
    assert abs(G.value - 6.67430e-11) < 2 * G.uncertainty
    assert 0 < G.uncertainty < 1e-14
    assert G.unit.is_equivalent(u.m**3 / u.kg / u.s**2)
    assert _expected("astropy.constants", "Gravitational constant G?") == "6.67430(15)e-11 m^3 kg^-1 s^-2 (CODATA 2018)"


def test_pint():
    import pint

    u = pint.UnitRegistry()
    assert u.Quantity(1, "kWh").to("joule").magnitude == 3_600_000.0
    assert _expected("pint", "1 kWh in joules?") == "3.6e6 J"


def test_chemformula():
    import chemformula

    f = chemformula.ChemFormula("H2SO4")
    assert dict(f.element) == {"H": 2, "S": 1, "O": 4}
    # 2*1.008 + 32.06 + 4*15.999 (IUPAC weights)
    assert abs(f.formula_weight - 98.072) < 0.01
    assert _expected("chemformula", "Composition and formula weight of H2SO4?") == "H:2 S:1 O:4, 98.072 g/mol"


def test_periodictable():
    import periodictable as pt

    assert pt.Fe.number == 26
    assert abs(pt.Fe.mass - 55.845) < 0.01
    assert pt.U.number == 92 and pt.U.name == "uranium"
    assert _expected("periodictable", "Fe atomic number and mass?") == "26 / 55.845"


def test_uncertainties():
    from uncertainties import ufloat

    r = ufloat(2.0, 0.1) * ufloat(3.0, 0.1)
    assert abs(r.nominal_value - 6.0) < 1e-9
    # independent errors: sigma = 6 * sqrt((0.1/2)^2 + (0.1/3)^2) ~= 0.3606
    assert abs(r.std_dev - 0.36055) < 1e-4
    assert _expected("uncertainties", "(2.0 +/- 0.1) * (3.0 +/- 0.1)?") == "6.0 +/- 0.3606 (independent errors)"

# -------------------------------------------------------- temporal/financial


def test_holidays():
    import holidays

    us = holidays.US(years=2025)
    assert "2025-07-04" in us
    assert us.get("2025-07-04") == "Independence Day"
    assert _expected("holidays", "Is 2025-07-04 a US holiday?") == "True (Independence Day)"


def test_dateutil():
    from dateutil.parser import parse

    assert parse("20250615T093000Z") == datetime(2025, 6, 15, 9, 30, tzinfo=timezone.utc)
    assert _expected("python-dateutil", "Parse '20250615T093000Z'?") == "2025-06-15 09:30:00+00:00"


def test_workalendar():
    from workalendar.usa import UnitedStates

    cal = UnitedStates()
    assert not cal.is_working_day(date(2025, 12, 25))  # Christmas
    assert cal.add_working_days(date(2025, 12, 25), 1) == date(2025, 12, 26)
    assert _expected("workalendar", "Next US working day after 2025-12-25?") == "2025-12-26"


def test_iso4217():
    import iso4217

    assert iso4217.raw_table["JPY"]["CcyMnrUnts"] == "0"
    assert iso4217.raw_table["USD"]["CcyNm"] == "US Dollar"
    assert iso4217.Currency.usd.value == "USD"
    assert _expected("iso4217", "Minor-unit decimals for JPY?") == "0"
    assert _expected("iso4217", "ISO 4217 name for USD?") == "US Dollar"

# ---------------------------------------------------------------- validate


def test_stdnum():
    from stdnum import iban, isbn, luhn

    assert iban.validate("DE89370400440532013000") == "DE89370400440532013000"
    try:
        iban.validate("DE89370400440532013001")
        raise AssertionError("invalid IBAN accepted")
    except iban.ValidationError:
        pass
    assert luhn.is_valid("4111111111111111")
    assert not luhn.is_valid("4111111111111112")
    assert isbn.is_valid("9783161484100")
    assert _expected("python-stdnum", "Is IBAN DE89370400440532013000 valid?") == "yes (spec example)"
    assert _expected("python-stdnum", "Does 4111111111111111 pass Luhn?") == "yes"
    assert _expected("python-stdnum", "Is ISBN-13 9783161484100 valid?") == "yes"


def test_phonenumbers():
    import phonenumbers

    p = phonenumbers.parse("+493012345678", "DE")
    assert p.country_code == 49
    assert phonenumbers.is_valid_number(p)
    assert phonenumbers.region_code_for_number(p) == "DE"
    assert phonenumbers.number_type(p) == phonenumbers.PhoneNumberType.FIXED_LINE
    assert _expected("phonenumbers", "Parse +493012345678 (DE)?") == "country_code=49, region=DE, type=FIXED_LINE"

# --------------------------------------------------------------------- io


def _minimal_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        # PNG chunk layout: length(4) + type(4) + data + crc32(type+data)(4)
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )


def test_python_magic():
    import magic

    assert magic.from_buffer(_minimal_png(), mime=True) == "image/png"
    assert magic.from_buffer(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n", mime=True) == "application/pdf"
    assert _expected("python-magic", "MIME of a minimal valid PNG?") == "image/png"


def test_filetype():
    import filetype

    kind = filetype.guess(_minimal_png())
    assert kind is not None and kind.mime == "image/png"
    kind = filetype.guess(b"%PDF-1.4\n")
    assert kind is not None and kind.mime == "application/pdf"
    assert _expected("filetype", "Format of 89 50 4E 47 0D 0A 1A 0A ...?") == "image/png"


def test_tldextract():
    from tldextract import TLDExtract

    ext = TLDExtract(suffix_list_urls=())  # bundled PSL snapshot only
    r = ext("www.example.co.uk")
    assert (r.subdomain, r.domain, r.suffix) == ("www", "example", "co.uk")
    assert _expected("tldextract", "Public suffix of www.example.co.uk?") == "co.uk"


def test_user_agents():
    from user_agents import parse

    ua = parse(
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
    assert ua.device.family == "iPhone"
    assert ua.os.family == "iOS"
    assert _expected("user-agents", "Parse an iPhone Safari 17 user-agent string?") == "device=iPhone, os=iOS"

# -------------------------------------------------------------- astronomy


def test_skyfield():
    from skyfield.api import load

    ts = load.timescale()
    # J2000.0 epoch: TT = 2451545.0 + 64.184 s (TT-UTC at the epoch)
    assert abs(ts.utc(2000, 1, 1, 12.0).tt - 2451545.0007429) < 1e-5
    assert _expected("skyfield", "TT Julian date at the J2000.0 epoch?") == "2451545.0007429 (TT-UTC = 64.184 s)"


def test_ephem_j2000_anchor():
    import ephem

    # float(Date) = JD - 2415020.0 (JD of 1900-01-01 12:00 UT); J2000 is exact
    assert float(ephem.Date("2000/1/1 12:00:00")) + 2415020.0 == 2451545.0
    assert _expected("ephem", "Julian date anchor: float(Date('2000/1/1 12:00:00')) + 2415020.0?") == "2451545.0 (J2000, exact)"


@pytest.mark.xfail(
    strict=False,
    reason=(
        "ephem 4.2.1 wheel returns a wrong moon phase (82.9 deg) for "
        "2025-06-15 12:00 UTC on this platform; independent oracles (pymeeus "
        "228.8 deg, astropy 228.2 deg) agree on ~228.8 deg. Canary test; "
        "see the ephem card in poor_richard.registry."
    ),
)
def test_ephem_moon_phase():
    import ephem

    got = ephem.Moon(ephem.Date("2025/6/15 12:00:00")).phase
    # 4.5 days past the 2025-06-11 full moon: waning gibbous, ~228.8 deg
    assert abs(got - 228.8) < 1.5


_ISS_LINE1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
_ISS_LINE2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"


def test_sgp4():
    from sgp4.api import Satrec

    satrec = Satrec.twoline2rv(_ISS_LINE1, _ISS_LINE2)
    assert satrec.satnum == 25544
    # TLE inclination 51.6416 deg (the record's own value)
    assert abs(math.degrees(satrec.inclo) - 51.6416) < 1e-4
    e, r, v = satrec.sgp4_tsince(0.0)  # at the TLE epoch
    assert e == 0
    radius = math.sqrt(r[0] ** 2 + r[1] ** 2 + r[2] ** 2)
    altitude = radius - 6378.137
    assert 300.0 < altitude < 450.0  # ISS LEO band for this 2008 TLE
    # subpoint latitude can never exceed the orbital inclination
    sublat = math.degrees(math.asin(r[2] / radius))
    assert abs(sublat) <= math.degrees(satrec.inclo) + 0.5
    assert _expected("sgp4", "ISS (TLE 25544, 2008) altitude at TLE epoch?") == "342 km (within 300-450 km LEO band)"


def test_astral():
    from astral import Observer
    from astral.sun import sunrise

    obs = Observer(latitude=40.7128, longitude=-74.0060)
    sunrise = sunrise(obs, date(2025, 6, 21))  # UTC by default
    # ~05:25 EDT on the June solstice = ~09:25 UTC at ~-74 deg longitude
    assert 9.0 <= sunrise.hour <= 10 and sunrise.tzinfo is not None
    assert _expected("astral", "Sunrise in New York (40.7128, -74.0060) on 2025-06-21?") == "09:25 UTC (~05:25 EDT, June solstice)"

# ------------------------------------------------------------------ colour


def test_colour():
    import colour

    # graph node is "CIE Lab"; convert() returns scale-1 values (L in [0, 1])
    lab = colour.convert([1.0, 0.0, 0.0], "sRGB", "CIE Lab") * 100
    # sRGB red: L* ~ 53.2, a* ~ 80.1, b* ~ 67.2
    assert abs(lab[0] - 53.23) < 0.5
    assert abs(lab[1] - 80.09) < 0.5
    assert abs(lab[2] - 67.20) < 0.5
    assert _expected("colour-science", "sRGB pure red -> CIE Lab?") == "(53.23, 80.09, 67.20)"

# --------------------------------------------------------------------- bio


def test_biopython():
    from Bio.Data import CodonTable
    from Bio.Seq import Seq

    tbl = CodonTable.unambiguous_dna_by_id[1]
    assert tbl.forward_table["ATG"] == "M"
    assert "TAA" in tbl.stop_codons
    assert str(Seq("ATGGCT").translate()) == "MA"
    assert _expected("biopython", "Codon ATG in the standard code?") == "M (methionine); TAA is a stop"

# ------------------------------------------------------- new candidate tier


def test_isodate():
    import isodate

    assert isodate.parse_date("2025-06-15") == date(2025, 6, 15)
    d = isodate.parse_duration("P1Y2M3DT4H5M6S")
    # Duration: years/months/days are ints; seconds is the total time seconds
    assert (d.years, d.months, d.days, d.seconds) == (1, 2, 3, 4 * 3600 + 5 * 60 + 6)
    assert _expected("isodate", "Parse ISO 8601 duration 'P1Y2M3DT4H5M6S'?") == "1y 2m 3d 4h 5m 6s"


def test_mimeparse():
    import mimeparse

    # note: best_match() is broken on py3 (uses dict.has_key); parse works
    assert mimeparse.parse_mime_type("text/html; charset=utf-8") == (
        "text",
        "html",
        {"charset": "utf-8"},
    )
    assert _expected("mimeparse", "Parse 'text/html; charset=utf-8'?") == "(text, html, {charset: utf-8})"


def test_molmass():
    import molmass

    # IUPAC weights: H2O = 2*1.008 + 15.999 = 18.015
    assert abs(molmass.Formula("H2O").mass - 18.015) < 0.01
    # glucose C6H12O6 = 6*12.011 + 12*1.008 + 6*15.999 = 180.156
    assert abs(molmass.Formula("C6H12O6").mass - 180.156) < 0.02
    assert _expected("molmass", "Molar mass of H2O?") == "18.015 g/mol"


def test_mido(tmp_path):
    import mido

    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=64, time=480))
    path = tmp_path / "test.mid"
    mid.save(str(path))  # save() needs a filename, not a file object
    mid2 = mido.MidiFile(str(path))
    msgs = [m for m in mid2.tracks[0] if isinstance(m, mido.Message)]
    assert [(m.type, m.note, m.velocity) for m in msgs] == [
        ("note_on", 60, 64),
        ("note_off", 60, 64),
    ]
    assert _expected("mido", "Round-trip a note_on(60)/note_off(60) MIDI file?") == "messages preserved on reload"


def test_particle():
    from particle import Particle

    # PDG code 13 = muon-, 11 = electron-; masses in MeV (PDG values)
    mu = Particle.from_pdgid(13)
    assert mu.name == "mu-"
    assert abs(mu.mass - 105.6583755) < 0.01
    e = Particle.from_pdgid(11)
    assert abs(e.mass - 0.51099895) < 0.001
    assert _expected("particle", "Particle with PDG code 13?") == "mu-, mass 105.6583755 MeV"


def test_geographiclib():
    from geographiclib.geodesic import Geodesic

    # Paris (48.8566, 2.3522) -> London (51.5074, -0.1278): ~343.9 km
    r = Geodesic.WGS84.Inverse(48.8566, 2.3522, 51.5074, -0.1278)
    assert abs(r["s12"] - 343923.0) < 1000.0
    assert _expected("geographiclib", "Great-circle distance Paris -> London?") == "343.9 km"


def test_bizdays():
    import bizdays

    # bridges to pandas_market_calendars via the PMC/ prefix
    cal = bizdays.Calendar.load("PMC/XNYS")
    assert cal.adjust_next(date(2025, 12, 25)) == date(2025, 12, 26)  # skip Christmas
    assert _expected("bizdays", "Next XNYS business day after 2025-12-25?") == "2025-12-26"


def test_charset_normalizer():
    import charset_normalizer as cn

    assert cn.from_bytes("héllo wörld, façade, naïve".encode("utf-8")).best().encoding == "utf_8"
    assert cn.from_bytes(b"plain ascii text, no accents at all").best().encoding == "ascii"
    assert _expected("charset-normalizer", "Encoding of a UTF-8 accented string?") == "utf_8"
    # single-byte family (cp125x) detection is ambiguous for short samples;
    # only the unambiguous cases are golden-tested


def test_idna():
    import idna

    assert idna.encode("例え.jp") == b"xn--r8jz45g.jp"
    assert idna.decode("xn--r8jz45g.jp") == "例え.jp"
    assert _expected("idna", "IDNA-encode the domain 例え.jp?") == "xn--r8jz45g.jp"


def test_pandas_market_calendars():
    import pandas_market_calendars as mcal

    xnys = mcal.get_calendar("XNYS")
    days = [d.date() for d in xnys.valid_days("2025-12-24", "2025-12-31")]
    # no Christmas (12/25), no weekends (12/27-28)
    assert days == [date(2025, 12, d) for d in (24, 26, 29, 30, 31)]
    assert _expected("pandas-market-calendars", "XNYS valid sessions 2025-12-24..31?") == "24, 26, 29, 30, 31 (no Christmas, no weekends)"


def test_chemicals():
    from chemicals import MW

    # water, CAS 7732-18-5
    assert abs(MW("7732-18-5") - 18.0153) < 0.001
    assert _expected("chemicals", "Molecular weight of water (CAS 7732-18-5)?") == "18.0153 g/mol"

# ------------------------------------------------------------------ hybrid


def test_starfile(tmp_path):
    import starfile

    star = (
        "data_block\n\n"
        "loop_\n"
        "_pixel.x\n_pixel.y\n_pixel.intensity\n"
        "1.0 2.0 100.0\n"
        "3.0 4.0 200.0\n"
    )
    p = tmp_path / "test.star"
    p.write_text(star)
    blk = starfile.read(p)
    assert list(blk.columns) == ["pixel.x", "pixel.y", "pixel.intensity"]
    assert blk["pixel.x"].tolist() == [1.0, 3.0]
    assert "loop_" in starfile.to_string(blk)
    assert _expected("starfile", "Parse a .star file with a 2-row pixel array?") == "columns pixel.x/pixel.y/pixel.intensity, values round-trip"


def test_czml3():
    import czml3

    pos = czml3.properties.Position(
        epoch="2025-01-01T00:00:00Z",
        cartesian=[-12981922.577142939, 4785512.491172238, 5338712.263513341],
    )
    pkt = czml3.Packet(id="test-sat", position=pos)
    d = pkt.model_dump(by_alias=True, exclude_none=True)
    assert d["id"] == "test-sat"
    assert d["position"]["epoch"] == "2025-01-01T00:00:00Z"
    assert d["position"]["cartesian"] == [
        -12981922.577142939,
        4785512.491172238,
        5338712.263513341,
    ]
    assert _expected("czml3", "Generate a CZML packet with one position sample?") == "{'id': ..., 'position': {'epoch': ..., 'cartesian': [x, y, z]}}"


def test_pysweph():
    import swisseph

    # 2025-06-15 12:00 UTC = JD 2460842.0 (2.6 days before the June solstice,
    # so the sun's ecliptic longitude is just under 90 degrees)
    jd = 2460842.0
    results, retflags, warn = swisseph.calc_ut(jd, swisseph.SUN)
    lon, lat, dist = results[:3]
    assert 84.5 < lon < 84.8
    assert abs(lat) < 0.001
    assert abs(dist - 1.015725) < 1e-4
    # pysweph (unlike pyswisseph) returns (results, retflags, warning_str)
    assert isinstance(warn, str)

    m_results, _, _ = swisseph.calc_ut(jd, swisseph.MOON)
    m_lon, m_lat, m_dist = m_results[:3]
    # cross-checked against astropy/JPL DE432 within ~2 arcsec
    assert abs(m_lon - 313.46463) < 0.01
    assert abs(m_lat - (-3.16)) < 0.01
    assert abs(m_dist - 0.002581) < 1e-4
    assert _expected("pysweph", "Sun ecliptic longitude 2025-06-15 12:00 UTC?") == "84.641 deg (JD 2460842.0, just under the 90 deg solstice)"


def test_financedatabase():
    import financedatabase
    from pathlib import Path

    data = Path(financedatabase.__file__).resolve().parent.parent / "compression"
    if not (data / "equities.bz2").exists():
        pytest.skip("financedatabase data not fetched (scripts/fetch_financedatabase.py)")
    # default mode downloads from GitHub per instantiation; use_local_location=True
    eq = financedatabase.Equities(use_local_location=True)
    aapl = eq.data.loc["AAPL"]  # symbol is the DataFrame index, not a column
    assert aapl["sector"] == "Information Technology"
    assert aapl["industry"] == "Electronic Equipment, Instruments & Components"
    cur = financedatabase.Currencies(use_local_location=True)
    pair = cur.data.loc["EURUSD=X"]
    assert (pair["base_currency"], pair["quote_currency"]) == ("EUR", "USD")
    assert _expected("financedatabase", "Sector of AAPL?") == "Information Technology"
    assert _expected("financedatabase", "Base/quote of EURUSD=X?") == "EUR / USD"
