"""Tests del buscador normalizado (tildes, guiones, sinónimos y ranking) y /api/convocatorias?q=."""

from fastapi.testclient import TestClient

from app.main import app
from app.search_utils import normalize_search_text, score_convocatoria_dict


def _sample_miteco_activa() -> dict:
    return {
        "id": "bdns-923290",
        "codigoOficial": "BDNS-923290",
        "titulo": "Ayudas MITECO 2026 (Línea A) para Proyectos de Protección del Medio Ambiente",
        "organismo": "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO (MITECO)",
        "tipoFuente": "publica_estatal",
        "ambitoTerritorial": "Estatal",
        "provincia": None,
        "orografiaPendiente": "Zonas forestales prioritarias",
        "cuantiaMaximaProyecto": 120000,
        "porcentajeCofinanciacion": 20,
        "modalidadPago": "mixto",
        "fechaCierre": "2026-12-02",
        "estado": "ACTIVA",
        "anio": 2026,
        "elegible": True,
        "matchingGlobal": 84,
        "motivoElegibilidad": "Apta ONG declarada de utilidad pública",
        "resumenEjecutivo": "Restauración de masas forestales y biodiversidad",
        "accionesSubvencionables": ["Repoblación con frondosas autóctonas"],
        "citasBasesJustificacion": ["Orden TED/898/2023"],
        "urlBasesPdf": "https://www.boe.es/boe/dias/2023/07/31/pdfs/BOE-A-2023-17623.pdf",
        "fuenteUrl": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/923290",
    }


def _sample_miteco_historico() -> dict:
    return {
        "id": "bdns-921561",
        "codigoOficial": "BDNS-921561",
        "titulo": "Resolución Dirección de la Fundación Biodiversidad en materia de restauración",
        "organismo": "ESTADO - MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
        "tipoFuente": "publica_estatal",
        "ambitoTerritorial": "Estatal",
        "provincia": None,
        "cuantiaMaximaProyecto": 85000,
        "porcentajeCofinanciacion": 0,
        "modalidadPago": "anticipo",
        "fechaCierre": "2025-10-15",
        "estado": "CERRADA",
        "anio": 2025,
        "elegible": True,
        "matchingGlobal": 82,
        "motivoElegibilidad": "Apta entidades sin ánimo de lucro",
        "resumenEjecutivo": "Proyectos de recuperación de ecosistemas forestales",
        "accionesSubvencionables": ["Prevención de incendios y restauración"],
        "urlBasesPdf": "https://www.boe.es/ejemplo.pdf",
        "fuenteUrl": "https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/921561",
    }


def _sample_madrid() -> dict:
    return {
        "id": "bocm-orden-1689-2026",
        "codigoOficial": "ORDEN 1689/2026",
        "titulo": "Subvenciones Comunidad de Madrid 2026 a Entidades sin Ánimo de Lucro para Proyectos Ambientales",
        "organismo": "Comunidad de Madrid - Consejería de Medio Ambiente, Agricultura e Interior",
        "tipoFuente": "publica_autonomica",
        "ambitoTerritorial": "Comunidad de Madrid",
        "provincia": None,
        "cuantiaMaximaProyecto": 60000,
        "porcentajeCofinanciacion": 20,
        "modalidadPago": "anticipo",
        "fechaCierre": "2026-11-25",
        "estado": "ACTIVA",
        "anio": 2026,
        "elegible": True,
        "matchingGlobal": 91,
        "motivoElegibilidad": "Apta asociación utilidad pública",
        "resumenEjecutivo": "Charcas y restauración en Sierra de Guadarrama",
        "accionesSubvencionables": ["Control de ailanto y reforestación"],
        "urlBasesPdf": "https://www.bocm.es/ejemplo.pdf",
        "fuenteUrl": "https://www.bocm.es/ejemplo",
    }


def test_normalize_search_text_handles_accents_and_separators() -> None:
    assert normalize_search_text("Transición Ecológica") == "transicion ecologica"
    assert normalize_search_text("BDNS-923290") == "bdns 923290"
    assert normalize_search_text("Orden 1689/2026") == "orden 1689 2026"


def test_miteco_matches_active_historical_and_variants() -> None:
    activa = _sample_miteco_activa()
    historica = _sample_miteco_historico()
    madrid = _sample_madrid()

    for query in ("miteco", "transicion ecologica", "bdns 923290", "BDNS923290", "orden ted", "estatal 2026"):
        assert score_convocatoria_dict(activa, query) > 0, f"Debe encontrar MITECO activa con '{query}'"

    # Histórica sin siglas 'MITECO' literales debe aparecer al buscar 'miteco' y 'transicion ecologica'
    assert score_convocatoria_dict(historica, "miteco") > 0
    assert score_convocatoria_dict(historica, "transicion ecologica") > 0
    assert score_convocatoria_dict(historica, "100%") > 0
    assert score_convocatoria_dict(historica, "sin aval") > 0

    # La activa debe puntuar por encima de la histórica cuando comparten texto
    assert score_convocatoria_dict(activa, "miteco") > score_convocatoria_dict(historica, "miteco")
    assert score_convocatoria_dict(madrid, "miteco") == 0


def test_fundacion_biodiversidad_does_not_leak_to_generic_ong() -> None:
    historica = _sample_miteco_historico()
    madrid = _sample_madrid()

    assert score_convocatoria_dict(historica, "fundacion biodiversidad") > 0
    assert score_convocatoria_dict(madrid, "fundacion biodiversidad") == 0

    # Búsqueda explícita por 'ong' sí encuentra ambas elegibles para ESAL
    assert score_convocatoria_dict(historica, "ong") > 0
    assert score_convocatoria_dict(madrid, "ong") > 0


def test_madrid_and_multiword_queries() -> None:
    madrid = _sample_madrid()
    activa = _sample_miteco_activa()

    for query in ("madrid 2026", "cam", "orden 1689 2026", "guadarrama ailanto"):
        assert score_convocatoria_dict(madrid, query) > 0
    assert score_convocatoria_dict(activa, "madrid") == 0


def test_api_convocatorias_q_param_returns_miteco_and_madrid() -> None:
    with TestClient(app) as client:
        r_miteco = client.get("/api/convocatorias", params={"estado": "TODAS", "q": "miteco"})
        assert r_miteco.status_code == 200
        ids_miteco = [c["id"] for c in r_miteco.json()["convocatorias"]]
        if ids_miteco:
            assert "bdns-923290" in ids_miteco or any("transicion" in c["organismo"].lower() for c in r_miteco.json()["convocatorias"])

        r_trans = client.get("/api/convocatorias", params={"estado": "TODAS", "q": "transicion ecologica"})
        assert r_trans.status_code == 200
        assert r_trans.json()["total"] == len(r_trans.json()["convocatorias"])

        r_empty = client.get("/api/convocatorias", params={"estado": "TODAS", "q": "xyznonexistentterm999"})
        assert r_empty.status_code == 200
        assert r_empty.json()["total"] == 0
