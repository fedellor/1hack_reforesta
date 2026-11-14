"""Comprehensive Geography & Ley 39/2015 (LPACAP Art. 30) Date Resolver Tests."""
from datetime import date
import pytest
from app.geo import CCAA_CATALOG, resolve_geography
from app.pipeline.date_resolver import (
    add_business_days,
    add_months_lpacap,
    compute_dates_and_status,
    is_business_day_es,
    parse_spanish_date,
    roll_to_next_business_day,
)


def test_geo_all_6_administrative_levels():
    # 1. UE
    ue = resolve_geography(organo="European Commission - CINEA", titulo="LIFE Nature & Biodiversity")
    assert ue.nivel_territorial == "UE"
    assert ue.ccaa_codigo == "EU"

    # 2. ESTADO (including Fundación Biodiversidad NOT misclassified as PRIVADA)
    fbio = resolve_geography(organo="MITECO - Fundación Biodiversidad", titulo="Restauración forestal")
    assert fbio.nivel_territorial == "ESTADO"
    assert fbio.ccaa_codigo == "ES"

    # 3. CCAA
    ccaa = resolve_geography(organo="Xunta de Galicia - Consellería do Medio Rural", titulo="Prevención de lumes")
    assert ccaa.nivel_territorial == "CCAA"
    assert ccaa.ccaa_codigo == "ES-GA"

    # 4. PROVINCIA (Diputación, Cabildo, Consell sin palabra Insular)
    prov = resolve_geography(organo="Diputación Provincial de Soria", titulo="Planes contra incendios")
    assert prov.nivel_territorial == "PROVINCIA"
    assert prov.ccaa_codigo == "ES-CL"
    assert prov.provincia_codigo == "ES-SO"

    consell = resolve_geography(organo="Consell de Mallorca", titulo="Prevenció d'incendis a la Serra de Tramuntana")
    assert consell.nivel_territorial == "PROVINCIA"
    assert consell.ccaa_codigo == "ES-IB"

    # 5. MUNICIPIO (Castellano, Gallego, Catalán y Euskera '-ko Udala')
    muni_gl = resolve_geography(organo="Concello de Lalín (Pontevedra)", titulo="Faixas de biomasa")
    assert muni_gl.nivel_territorial == "MUNICIPIO"
    assert muni_gl.ccaa_codigo == "ES-GA"
    assert muni_gl.municipio_nombre == "Lalín" or muni_gl.municipio_nombre == "Lalin"

    muni_eu = resolve_geography(organo="Oñatiko Udala", titulo="Baso-berritze diru-laguntzak")
    assert muni_eu.nivel_territorial == "MUNICIPIO"
    assert muni_eu.ccaa_codigo == "ES-PV"
    assert muni_eu.municipio_nombre == "Onati"

    # Municipal fallback in title when organo is generic BDNS
    muni_title = resolve_geography(
        organo="Entidades Locales (BDNS)",
        titulo="Subvenciones del Ayuntamiento de Cuenca para repoblación forestal",
    )
    assert muni_title.nivel_territorial == "MUNICIPIO"
    assert muni_title.ccaa_codigo == "ES-CM"

    # 6. PRIVADA
    priv = resolve_geography(organo="Fundación Daniel y Nina Carasso", titulo="Resiliencia agroecológica y bosques")
    assert priv.nivel_territorial == "PRIVADA"
    assert priv.ccaa_codigo == "ES"


def test_geo_acronym_word_boundary_no_false_ccaa():
    """
    Regression test: ensure short bulletin acronyms ('bon', 'bor', 'dog', 'boa')
    do NOT falsely match inside Spanish words like 'carbono' or 'colaboración'.
    """
    carbono = resolve_geography(
        organo="Fundación Ecodes / Consorcio Nacional",
        titulo="Programa de sumidero de carbono y bonificación ambiental",
    )
    assert carbono.ccaa_codigo != "ES-NC"  # Must NOT match 'bon' inside 'carbono'

    arbor = resolve_geography(
        organo="Red Española de Bosques",
        titulo="Colaboración y elaboración de estudios sobre arboricultura urbana",
    )
    assert arbor.ccaa_codigo != "ES-RI"  # Must NOT match 'bor' inside 'colaboración'/'arboricultura'


@pytest.mark.parametrize(
    ("nuts", "expected_ccaa"),
    [
        ("ES61", "ES-AN"),
        ("ES24", "ES-AR"),
        ("ES12", "ES-AS"),
        ("ES13", "ES-CB"),
        ("ES63", "ES-CE"),
        ("ES41", "ES-CL"),
        ("ES42", "ES-CM"),
        ("ES70", "ES-CN"),
        ("ES51", "ES-CT"),
        ("ES43", "ES-EX"),
        ("ES11", "ES-GA"),
        ("ES53", "ES-IB"),
        ("ES62", "ES-MC"),
        ("ES30", "ES-MD"),
        ("ES64", "ES-ML"),
        ("ES22", "ES-NC"),
        ("ES21", "ES-PV"),
        ("ES23", "ES-RI"),
        ("ES52", "ES-VC"),
    ],
)
def test_geo_all_19_nuts_codes(nuts: str, expected_ccaa: str):
    assert expected_ccaa in CCAA_CATALOG
    info = resolve_geography(organo="Gobierno Regional", nuts_code=nuts)
    assert info.ccaa_codigo == expected_ccaa


def test_multilingual_date_parsing():
    assert parse_spanish_date("2026-11-15") == date(2026, 11, 15)
    assert parse_spanish_date("15/11/2026") == date(2026, 11, 15)
    assert parse_spanish_date("15.11.2026") == date(2026, 11, 15)
    assert parse_spanish_date("20 de julio de 2023") == date(2023, 7, 20)
    assert parse_spanish_date("15 d'octubre de 2026") == date(2026, 10, 15)
    assert parse_spanish_date("12 de outubro do 2026") == date(2026, 10, 12)
    assert parse_spanish_date("15 November 2026") == date(2026, 11, 15)
    assert parse_spanish_date("November 15, 2026") == date(2026, 11, 15)
    assert parse_spanish_date("not-a-date") is None


def test_lpacap_art30_edge_cases():
    # 1. Sunday holiday transferred to Monday: Nov 1, 2026 is Sunday -> Monday Nov 2 is non-working!
    assert is_business_day_es(date(2026, 11, 1)) is False
    assert is_business_day_es(date(2026, 11, 2)) is False
    assert is_business_day_es(date(2026, 11, 3)) is True

    # 2. Month fecha-a-fecha without equivalent day (Jan 31 + 1 month -> Feb 28/29 + rollover)
    # 2025-01-31 + 1 month -> 2025-02-28 (Friday, working day)
    assert add_months_lpacap(date(2025, 1, 31), 1) == date(2025, 2, 28)
    # 2026-01-31 + 1 month -> 2026-02-28 (Saturday) -> rolls to Monday March 2!
    assert add_months_lpacap(date(2026, 1, 31), 1) == date(2026, 3, 2)

    # 3. Catalan regional holiday: Sept 11 (Diada de Catalunya)
    assert is_business_day_es(date(2026, 9, 11), ccaa_codigo="ES-CT") is False
    assert is_business_day_es(date(2026, 9, 11), ccaa_codigo="ES-MD") is True
    assert roll_to_next_business_day(date(2026, 9, 11), ccaa_codigo="ES-CT") == date(2026, 9, 14)

    # 4. Catalan deadline clause: Sept 10 pub + 'día siguiente' -> PROXIMA on Sept 10, ACTIVA on Sept 11+
    ca_res = compute_dates_and_status(
        fecha_publicacion=date(2026, 9, 10),
        plazo_texto_original="2 dies hàbils a comptar des del dia següent",
        ccaa_codigo="ES-CT",
        today=date(2026, 9, 10),
    )
    # Sept 11 (Diada CT), Sept 12 (Sat), Sept 13 (Sun) skipped -> Day 1 = Sept 14, Day 2 = Sept 15
    assert ca_res.fecha_fin_solicitud == date(2026, 9, 15)
    assert ca_res.estado == "PROXIMA"

    ca_active = compute_dates_and_status(
        fecha_publicacion=date(2026, 9, 10),
        plazo_texto_original="2 dies hàbils a comptar des del dia següent",
        ccaa_codigo="ES-CT",
        today=date(2026, 9, 14),
    )
    assert ca_active.estado == "ACTIVA"
    assert ca_active.dias_restantes == 1

    # 5. PROXIMA status when fecha_inicio > today
    prox = compute_dates_and_status(
        fecha_publicacion=date(2026, 11, 1),
        fecha_inicio_solicitud=date(2026, 11, 20),
        fecha_fin_solicitud=date(2026, 12, 20),
        today=date(2026, 11, 14),
    )
    assert prox.estado == "PROXIMA"
    assert prox.dias_restantes == 36
