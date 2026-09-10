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


def test_babel():
    from babel import Locale
    from babel.dates import format_date
    from babel.numbers import format_currency, format_decimal

    # CLDR display name for 'de' in English; cross-checked against pycountry
    # (ISO 639-1 'de' -> German, same source value)
    assert Locale("de").get_display_name("en") == "German"
    # Russian plural categories per the CLDR rules: n=1 -> one;
    # n%10 in 2..4 (but not 12..14) -> few; n%10==0 or 5..9 or n%100 in 11..14 -> many
    plural = Locale("ru").plural_form  # 2.18: property returning a callable PluralRule
    assert (plural(2), plural(5), plural(21), plural(1)) == ("few", "many", "one", "one")
    assert format_decimal(1234.5, locale="en_US") == "1,234.5"
    # CLDR de_DE currency output uses U+00A0 (no-break space) before the symbol
    assert format_currency(1234.5, "USD", locale="de_DE").replace("\xa0", " ") == "1.234,50 $"
    assert format_date(datetime(2026, 2, 5), "full", locale="en") == "Thursday, February 5, 2026"
    assert _expected("babel", "English display name for locale 'de'?") == "German"
    assert _expected("babel", "Russian plural categories for 2, 5, 21?") == "few, many, one (CLDR ru rules)"
    assert _expected("babel", "Format 1234.5 in en_US?") == "1,234.5"
    assert _expected("babel", "Format 1234.50 USD in de_DE?") == "1.234,50 $ (U+00A0 no-break space before the symbol)"
    assert _expected("babel", "Full date for 2026-02-05 in 'en'?") == "Thursday, February 5, 2026"


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


def test_h3():
    import h3

    # Expected values are the H3 v4 spec's own regression vectors
    # (uber/h3 v4.5.0, tests/cli/*.txt - the C reference impl's golden data).
    assert h3.latlng_to_cell(20, 123, 2) == "824b9ffffffffff"
    lat, lng = h3.cell_to_latlng("8928342e20fffff")
    assert abs(lat - 37.5012466151) < 1e-9
    assert abs(lng - (-122.5003039349)) < 1e-9
    assert h3.get_base_cell_number("85283473fffffff") == 20
    assert h3.grid_distance("85283473fffffff", "8528342bfffffff") == 2
    assert _expected("h3", "H3 cell at res 2 for (20, 123)?") == "824b9ffffffffff"
    assert _expected("h3", "Center of H3 cell 8928342e20fffff?") == "(37.5012466151, -122.5003039349)"
    assert _expected("h3", "Base cell of 85283473fffffff?") == "20"
    assert _expected("h3", "Grid distance 85283473fffffff -> 8528342bfffffff?") == "2"


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

def test_ambiance():
    from ambiance import Atmosphere

    # ISA sea level: values defined by ICAO Doc 7488 / ISO 2533
    sea = Atmosphere(0)
    assert sea.temperature[0] == 288.15
    assert sea.pressure[0] == 101325.0
    assert abs(sea.density[0] - 1.225) < 1e-6
    # speed of sound: sqrt(gamma*R*T0) = sqrt(1.4 * 287.05287 * 288.15)
    assert abs(sea.speed_of_sound[0] - 340.294) < 0.01

    # tropopause: P = 22632 Pa is the ISA table value at the top of the
    # troposphere (geopotential 11 km); T there is exactly 216.65 K
    tp = Atmosphere.from_pressure(22632.0)
    assert abs(tp.temperature[0] - 216.65) < 1e-6
    assert abs(tp.h[0] - 11019.1) < 1.0  # geometric; geopotential is 11000 m

    # cross-check against the closed-form ISA troposphere equation
    # P = P0 * (T/T0)^(g0/(R*L)), independent of the package's implementation
    g0, R, gamma, T0, P0, L, Re = 9.80665, 287.05287, 1.4, 288.15, 101325.0, 0.0065, 6356766.0
    H = 10000.0  # geopotential height
    h = H / (1.0 - H / Re)  # -> geometric (Atmosphere takes geometric input)
    T = T0 - L * H
    P = P0 * (T / T0) ** (g0 / (R * L))
    at = Atmosphere(h)
    assert abs(at.temperature[0] - T) < 1e-6
    assert abs(at.pressure[0] - P) < 1e-3  # ~26436.2 Pa
    assert abs(at.density[0] - P / (R * T)) < 1e-9
    assert abs(at.speed_of_sound[0] - (gamma * R * T) ** 0.5) < 1e-6

    assert _expected("ambiance", "ISA sea-level temperature?") == "288.15 K (15 degC, exact by definition)"
    assert _expected("ambiance", "ISA sea-level pressure and density?") == "101325 Pa, 1.225 kg/m3 (exact by definition)"
    assert _expected("ambiance", "ISA speed of sound at sea level?") == "340.29 m/s (sqrt(1.4 * R * T0))"
    assert _expected("ambiance", "ISA temperature at the tropopause (22632 Pa)?") == "216.65 K (11019 m geometric = 11 km geopotential)"

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


def test_convertdate():
    import convertdate.french_republican as french
    import convertdate.hebrew as hebrew
    import convertdate.islamic as islamic
    import convertdate.julian as julian
    import convertdate.mayan as mayan

    # Gregorian<->Julian offset is 13 days for 1900-2100
    assert julian.from_gregorian(2000, 2, 28) == (2000, 2, 15)
    assert julian.to_gregorian(2000, 2, 15) == (2000, 2, 28)
    # 1 Tishrei 5785 = Rosh Hashanah 5785, first day (published date:
    # Wikipedia "2024 in Israel" — Rosh Hashanah 3 Oct, Yom Kippur 12 Oct)
    assert hebrew.from_gregorian(2024, 10, 3) == (5785, 7, 1)
    # Hijra epoch: 1 Muharram 1 AH = 622-07-19 proleptic Gregorian (tabular)
    assert islamic.from_gregorian(622, 7, 19) == (1, 1, 1)
    # 1 Brumaire Year I = 1792-09-22 (the Republic proclaimed)
    assert french.from_gregorian(1792, 9, 22) == (1, 1, 1)
    # End of the 13th b'ak'tun = 2012-12-21 (GMT correlation constant 584283)
    assert mayan.from_gregorian(2012, 12, 21) == (13, 0, 0, 0, 0)
    assert mayan.to_gregorian(13, 0, 0, 0, 0) == (2012, 12, 21)
    assert _expected("convertdate", "What is 2000-02-28 in the Julian calendar?") == "2000-02-15 (13 days behind, 1900–2100)"
    assert _expected("convertdate", "Hebrew date for 2024-10-03?") == "1 Tishrei 5785 (first day of Rosh Hashanah)"
    assert _expected("convertdate", "Islamic date for 622-07-19 (Gregorian)?") == "1 Muharram 1 AH (Hijra epoch)"
    assert _expected("convertdate", "French Republican date for 1792-09-22?") == "1 Brumaire Year I"
    assert _expected("convertdate", "Mayan Long Count for 2012-12-21?") == "13.0.0.0.0 (end of the 13th b'ak'tun; GMT correlation)"


def test_icalendar():
    import zoneinfo
    from datetime import timedelta

    from icalendar import Calendar, Event
    from icalendar.prop import vDate, vDuration

    # RFC 5545 section 3.8.3 example VEVENT (values from the RFC itself)
    cal = Calendar.from_ical(
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//EXAMPLE//EN\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:20070907T132945Z-123456@EXAMPLE.COM\r\n"
        "DTSTAMP:20070907T132945Z\r\n"
        "DTSTART:20070908T130000Z\r\n"
        "DTEND:20070908T150000Z\r\n"
        "SUMMARY:Meeting with Jeffrey\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR"
    )
    ev = cal.walk("VEVENT")[0]
    assert str(ev["SUMMARY"]) == "Meeting with Jeffrey"
    assert ev["DTSTART"].dt == datetime(2007, 9, 8, 13, 0, tzinfo=timezone.utc)
    assert ev["DTSTART"].to_ical() == b"20070908T130000Z"
    assert _expected("icalendar", "SUMMARY of the RFC 5545 example VEVENT?") == "Meeting with Jeffrey (2007-09-08 13:00–15:00 UTC, §3.8.3)"

    # generation: exact content lines per RFC 5545 section 3.1/3.3.5
    e = Event()
    e.add("SUMMARY", "Planning Meeting")
    e.add("DTSTART", datetime(2008, 3, 15, 13, 30, tzinfo=timezone.utc))
    e.add("DTEND", datetime(2008, 3, 15, 15, 0, tzinfo=timezone.utc))
    assert e.to_ical() == (
        b"BEGIN:VEVENT\r\n"
        b"SUMMARY:Planning Meeting\r\n"
        b"DTSTART:20080315T133000Z\r\n"
        b"DTEND:20080315T150000Z\r\n"
        b"END:VEVENT\r\n"
    )
    assert _expected("icalendar", "Content line for a UTC DTSTART of 2008-03-15 13:30?") == "DTSTART:20080315T133000Z (CRLF-terminated bytes)"

    # RFC 5545 section 3.6.1 VTIMEZONE example: America/New_York EST5EDT
    tz = Calendar.from_ical(
        "BEGIN:VTIMEZONE\r\n"
        "TZID:America/New_York\r\n"
        "BEGIN:STANDARD\r\n"
        "DTSTART:19701025T020000\r\n"
        "RRULE:FREQ=YEARLY;BYDAY=5SU;BYMONTH=10\r\n"
        "TZOFFSETFROM:-0400\r\n"
        "TZOFFSETTO:-0500\r\n"
        "TZNAME:EST\r\n"
        "END:STANDARD\r\n"
        "BEGIN:DAYLIGHT\r\n"
        "DTSTART:19700308T020000\r\n"
        "RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3\r\n"
        "TZOFFSETFROM:-0500\r\n"
        "TZOFFSETTO:-0400\r\n"
        "TZNAME:EDT\r\n"
        "END:DAYLIGHT\r\n"
        "END:VTIMEZONE"
    ).walk("VTIMEZONE")[0]
    assert str(tz["TZID"]) == "America/New_York"
    assert tz.walk("STANDARD")[0]["TZOFFSETTO"].to_ical() == "-0500"  # EST
    assert tz.walk("DAYLIGHT")[0]["TZOFFSETTO"].to_ical() == "-0400"  # EDT
    # cross-check against the IANA oracle (stdlib zoneinfo)
    ny = zoneinfo.ZoneInfo("America/New_York")
    assert datetime(2007, 9, 8, 12, tzinfo=ny).utcoffset() == timedelta(hours=-4)
    assert datetime(2007, 1, 15, 12, tzinfo=ny).utcoffset() == timedelta(hours=-5)
    assert _expected("icalendar", "Offsets in the RFC 5545 VTIMEZONE example (America/New_York)?") == "EST −0500, EDT −0400 (matches IANA zoneinfo)"

    # DATE-TIME / DURATION property values (RFC 5545 sections 3.3.5/3.3.6)
    assert vDuration.from_ical("PT2H30M") == timedelta(hours=2, minutes=30)
    assert vDate.from_ical("20070908") == date(2007, 9, 8)
    assert _expected("icalendar", "How does the DURATION value 'PT2H30M' parse?") == "timedelta(hours=2, minutes=30)"


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


def test_pymeeus():
    from pymeeus import Sun, Moon
    from pymeeus.Epoch import Epoch

    # 2025-06-15 12:00 UTC; utc=True converts to TT (JDE), TT-UTC = 69.184 s
    e = Epoch(2025, 6, 15, 12, utc=True)
    slon, slat, sr = Sun.Sun.apparent_geocentric_position(e)
    # 2.6 days before the June solstice: just under 90 deg; cross-checked
    # against pysweph (Swiss Ephemeris) to 0.001 deg
    assert abs(float(slon) - 84.641) < 0.01
    assert abs(float(slat)) < 0.01
    assert abs(sr - 1.015725) < 1e-4  # ~1.016 AU, near aphelion (July 4)

    mlon, mlat, mdist, mpar = Moon.Moon.geocentric_ecliptical_pos(e)
    # cross-checked against pysweph (313.46463 / -3.16); the elongation is
    # the 228.8 deg that the ephem xfail canary expects (waning gibbous,
    # 4.5 days past the 2025-06-11 full moon)
    assert abs(float(mlon) - 313.464) < 0.01
    assert abs(float(mlat) + 3.157) < 0.01
    assert abs((float(mlon) - float(slon)) % 360 - 228.82) < 0.1
    assert 380000 < mdist < 390000  # km, mid-month
    assert 0.8 < Moon.Moon.illuminated_fraction_disk(e) < 0.9

    # 2025 spring equinox: published 2025-03-20 09:01:54 UTC; JDE is in TT
    eq = Sun.Sun.get_equinox_solstice(2025, "spring")
    y, m, d, h, mi, s = eq.get_full_date()
    assert (y, m, d, h, mi) == (2025, 3, 20, 9, 2) and s < 45

    # J2000.0 anchor: JD 2451545.0 is 2000-01-01 12:00 TT by definition
    assert Epoch(2451545.0).get_full_date() == (2000, 1, 1, 12, 0, 0.0)
    assert _expected("pymeeus", "Sun apparent ecliptic longitude 2025-06-15 12:00 UTC?") == "84.641 deg (just under the 90 deg solstice; agrees with pysweph to 0.001 deg)"
    assert _expected("pymeeus", "Moon geocentric ecliptic position 2025-06-15 12:00 UTC?") == "lon 313.464 deg, lat -3.157 deg (elongation 228.8 deg - the ephem canary's value)"
    assert _expected("pymeeus", "2025 spring equinox (UTC)?") == "2025-03-20 09:01:28 (published 09:01:54 UTC)"
    assert _expected("pymeeus", "Julian date of the J2000.0 epoch?") == "2451545.0 (2000-01-01 12:00 TT, exact by definition)"

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


# ---------------------------------------------------------------- formats/io


def test_email_validator():
    from email_validator import EmailSyntaxError, validate_email

    # RFC 2606 reserves example.com for documentation; the address is the
    # canonical RFC 5322 simple example
    r = validate_email("postmaster@example.com", check_deliverability=False)
    assert (r.local_part, r.domain) == ("postmaster", "example.com")
    assert _expected("email-validator", "Is postmaster@example.com a valid RFC 5322 address?") == "yes"

    # RFC 5322 section 3.2.3 dot-atom example (user.name+tag+spec@example.com)
    r = validate_email("user.name+tag@example.com", check_deliverability=False)
    assert r.normalized == "user.name+tag@example.com"
    assert _expected("email-validator", "Is user.name+tag@example.com valid?") == "yes (+ is a valid atext)"

    # underscores are not allowed in domain labels (RFC 5322 dot-atom)
    with pytest.raises(EmailSyntaxError):
        validate_email("user@exam_ple.com", check_deliverability=False)
    assert _expected("email-validator", "Is user@exam_ple.com valid?") == "no (underscore not allowed in domain labels)"

    # empty local part is rejected by the RFC 5322 grammar
    with pytest.raises(EmailSyntaxError):
        validate_email("@example.com", check_deliverability=False)
    assert _expected("email-validator", "Is @example.com valid?") == "no (empty local part)"

    # normalization: domain lowercased, local part keeps case (RFC 5321)
    r = validate_email("First.Local@Example.COM", check_deliverability=False)
    assert r.normalized == "First.Local@example.com"
    assert _expected("email-validator", "Normalize First.Local@Example.COM?") == "First.Local@example.com (domain lowercased, local case kept)"

    # cross-check vs the idna card: xn--r8jz45g.jp is the IDNA2008 encoding of
    # 例え.jp, and .normalized decodes the domain back to the Unicode form
    r = validate_email("user@xn--r8jz45g.jp", check_deliverability=False)
    assert r.domain == "例え.jp"
    assert _expected("email-validator", "Domain of user@xn--r8jz45g.jp?") == "例え.jp (IDNA2008-decoded)"
