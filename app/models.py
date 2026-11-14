"""Database models and API response schemas for 1hack_reforesta."""
from datetime import date, datetime, timezone
from typing import Any
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import Field, SQLModel


class Opportunity(SQLModel, table=True):
    """Unified model for grants, subsidies, public tenders, EU calls and private funds (desde 2016)."""

    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opp_estado_ccaa", "estado", "ccaa_codigo"),
        Index("ix_opp_estado_prioridad", "estado", "prioridad_score"),
        Index("ix_opp_anio_estado", "anio_convocatoria", "estado"),
        Index("ix_opp_nivel_ccaa", "nivel_territorial", "ccaa_codigo"),
        Index("ix_opp_relevancia_estado", "relevancia_tipo", "estado"),
    )

    id: str = Field(primary_key=True, index=True)
    codigo_oficial: str = Field(index=True)
    fuente: str = Field(index=True)  # BDNS | PLACSP | BOE | EU_SEDIA | BOLETIN_CCAA | FUENTES_PDF
    tipo_oportunidad: str = Field(index=True)  # SUBVENCION | LICITACION | PROGRAMA_UE | CONVOCATORIA_PRIVADA | CONVENIO
    estado: str = Field(index=True)  # ACTIVA | PROXIMA | CERRADA
    dias_restantes: int | None = Field(default=None, index=True)

    # Materialized Strategic Prioritization (Indexed in SQL for O(log N) sorting)
    prioridad_score: int = Field(default=50, index=True)
    prioridad_nivel: str = Field(default="MEDIA", index=True)  # CRITICA | ALTA | MEDIA | BAJA | HISTORICO
    estado_interno: str = Field(default="nueva", index=True)  # nueva | priorizada | en_preparacion | presentada | descartada

    # Layer 1 & Layer 2 Relevance
    relevancia_tipo: str = Field(index=True)  # DIRECTA | INDIRECTA_ELEGIBLE
    relevancia_score: int = Field(default=75, index=True)
    score_capa1: int = Field(default=0)
    categorias: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    justificacion_juez: str = Field(default="", sa_column=Column(Text))

    # Content (Always normalized/translated to Spanish in titulo_limpio & resumen)
    idioma_original: str = Field(default="es")
    titulo_limpio: str = Field(sa_column=Column(Text))
    titulo_original: str = Field(sa_column=Column(Text))
    resumen: str = Field(default="", sa_column=Column(Text))

    # Geography & Terrain
    nivel_territorial: str = Field(index=True)  # UE | ESTADO | CCAA | PROVINCIA | MUNICIPIO | PRIVADA
    ccaa_codigo: str = Field(index=True)  # ES-AN..ES-VC, ES, EU
    ccaa_nombre: str = Field(default="")
    provincia_codigo: str | None = Field(default=None, index=True)
    provincia_nombre: str | None = Field(default=None)
    municipio_nombre: str | None = Field(default=None)
    orografia_pendiente: str = Field(default="pendiente_media")  # llano | pendiente_media | alta_montana | indiferente

    # Issuing Body
    organo_convocante: str = Field(default="", sa_column=Column(Text))
    unidad_convocante: str | None = Field(default=None)

    # Financials & Treasury Viability
    presupuesto_total: float | None = Field(default=None, index=True)
    importe_max_proyecto: float | None = Field(default=None)
    importe_max_beneficiario: float | None = Field(default=None)
    porcentaje_max_financiacion: float | None = Field(default=None)
    modalidad_pago: str = Field(default="mixto")  # anticipo | reembolso | mixto
    pago_anticipado_sin_aval: bool = Field(default=False)
    moneda: str = Field(default="EUR")
    cofinanciado_ue: bool = Field(default=False, index=True)
    fondo_ue: str | None = Field(default=None)

    # Beneficiaries, Requirements, Citations & Dealbreakers
    beneficiarios_tipos: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    sector_economico_original: str | None = Field(default=None)
    requisitos_resumen: str = Field(default="", sa_column=Column(Text))
    gastos_subvencionables: str | None = Field(default=None, sa_column=Column(Text))
    criterios_valoracion: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    citas_bases: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    dealbreakers: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    matching_lineas: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))

    # Dates
    anio_convocatoria: int = Field(index=True)
    fecha_publicacion: date | None = Field(default=None, index=True)
    fecha_inicio_solicitud: date | None = Field(default=None)
    fecha_fin_solicitud: date | None = Field(default=None, index=True)
    plazo_texto_original: str | None = Field(default=None)
    es_plazo_calculado: bool = Field(default=False)

    # Official Links
    url_ficha_oficial: str = Field(default="")
    url_tramitacion: str | None = Field(default=None)
    url_bases_reguladoras: str | None = Field(default=None)
    url_boletin_extracto: str | None = Field(default=None)
    archivo_fuente_local: str | None = Field(default=None)

    # Audit
    metodo_evaluacion: str = Field(default="HYBRID_GEMINI")  # HYBRID_GEMINI | HYBRID_HEURISTIC
    fecha_ingesta: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_api_dict(self) -> dict[str, Any]:
        """Serialize to the canonical nested JSON contract agreed with the Frontend, including Strategic Prioritization."""
        from app.pipeline.metadata_extractor import build_frontend_metadata_bundle
        from app.pipeline.prioritizer import calculate_priority

        front_meta = build_frontend_metadata_bundle(self)
        ubic = front_meta["ubicacion"]
        plaz = front_meta["plazos"]
        din = front_meta["dinero"]

        prio = calculate_priority(
            estado=self.estado,
            dias_restantes=self.dias_restantes,
            relevancia_tipo=self.relevancia_tipo,
            relevancia_score=self.relevancia_score,
            beneficiarios_tipos=self.beneficiarios_tipos or [],
            porcentaje_financiacion=din["porcentaje_max_financiacion"],
            presupuesto_total=din["presupuesto_total"],
            importe_max_proyecto=din["importe_max_proyecto"],
            nivel_territorial=self.nivel_territorial,
        )
        elig, merged_dealbreakers = self._evaluate_reforesta_eligibility()
        return {
            "id": self.id,
            "codigo_oficial": self.codigo_oficial,
            "tipo_oportunidad": self.tipo_oportunidad,
            "estado": self.estado,
            "estado_interno": self.estado_interno,
            "dias_restantes": self.dias_restantes,
            "dias_habiles_restantes": plaz["dias_habiles_restantes"],
            "idioma_original": self.idioma_original,
            "priorizacion": {
                "score": prio.prioridad_score,
                "nivel": prio.prioridad_nivel,
                "urgencia_plazo": prio.urgencia_label,
                "recomendacion_tactica": prio.recomendacion_tactica,
            },
            "relevancia": {
                "tipo": self.relevancia_tipo,
                "score": self.relevancia_score,
                "score_capa1": self.score_capa1,
                "categorias": self.categorias or [],
                "justificacion": self.justificacion_juez,
                "matching_lineas": self.matching_lineas or self._default_matching_lineas(),
            },
            "titulo_limpio": self.titulo_limpio,
            "titulo_original": self.titulo_original,
            "resumen": self.resumen,
            "ambito_geografico": {
                "nivel": self.nivel_territorial,
                "aplica_en_espana": ubic["aplica_en_espana"],
                "es_ayuda_extranjera_para_espana": ubic["es_ayuda_extranjera_para_espana"],
                "pais_codigo": ubic["pais_codigo"],
                "ccaa_codigo": self.ccaa_codigo,
                "ccaa_nombre": self.ccaa_nombre,
                "nuts_codigo": ubic["nuts_codigo"],
                "provincia_codigo": self.provincia_codigo,
                "provincia_nombre": self.provincia_nombre,
                "municipio": self.municipio_nombre,
                "espacio_natural_o_comarca": ubic["espacio_natural_o_comarca"],
                "orografia_pendiente": self.orografia_pendiente,
                "coordenadas_mapa": ubic["coordenadas_mapa"],
                "etiqueta_front": ubic["etiqueta_front"],
            },
            "organo_convocante": {
                "nivel_administracion": self.nivel_territorial,
                "administracion": self.organo_convocante,
                "unidad": self.unidad_convocante,
            },
            "economia": {
                "presupuesto_total": din["presupuesto_total"],
                "importe_max_proyecto": din["importe_max_proyecto"],
                "importe_max_beneficiario": din["importe_max_beneficiario"],
                "importe_min_proyecto": din["importe_min_proyecto"],
                "ayuda_por_hectarea_euros": din["ayuda_por_hectarea_euros"],
                "porcentaje_max_financiacion": din["porcentaje_max_financiacion"],
                "porcentaje_cofinanciacion_requerida": din["porcentaje_cofinanciacion_requerida"],
                "modalidad_pago": self.modalidad_pago,
                "pago_anticipado_sin_aval": self.pago_anticipado_sin_aval,
                "moneda": self.moneda,
                "cofinanciado_ue": self.cofinanciado_ue,
                "fondo_ue": self.fondo_ue,
                "etiqueta_front": din["etiqueta_front"],
            },
            "beneficiarios": {
                "tipos": self.beneficiarios_tipos or elig.beneficiarios_tipos,
                "elegible_reforesta": elig.elegible,
                "motivo_elegibilidad": elig.motivo_elegibilidad,
                "descripcion_requisitos": self.requisitos_resumen,
                "gastos_subvencionables": self.gastos_subvencionables,
                "criterios_valoracion": self.criterios_valoracion or [],
                "citas_bases": self.citas_bases or [],
                "dealbreakers": merged_dealbreakers,
            },
            "fechas": {
                "anio_convocatoria": self.anio_convocatoria,
                "fecha_publicacion": self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
                "fecha_inicio_solicitud": self.fecha_inicio_solicitud.isoformat() if self.fecha_inicio_solicitud else None,
                "fecha_fin_solicitud": self.fecha_fin_solicitud.isoformat() if self.fecha_fin_solicitud else None,
                "dias_naturales_restantes": plaz["dias_naturales_restantes"],
                "dias_habiles_restantes": plaz["dias_habiles_restantes"],
                "plazo_texto_original": self.plazo_texto_original,
                "es_plazo_calculado": self.es_plazo_calculado,
                "etiqueta_front": plaz["etiqueta_front"],
            },
            "metadatos_front": front_meta,
            "enlaces": {
                "url_ficha_oficial": self.url_ficha_oficial,
                "url_tramitacion": self.url_tramitacion,
                "url_bases_reguladoras": self.url_bases_reguladoras,
                "url_boletin_extracto": self.url_boletin_extracto,
                "archivo_fuente_local": self.archivo_fuente_local,
            },
            "metadatos_fuente": {
                "fuente_primaria": self.fuente,
                "metodo_evaluacion": self.metodo_evaluacion,
                "fecha_ingesta": self.fecha_ingesta.isoformat() if self.fecha_ingesta else None,
            },
        }

    def _evaluate_reforesta_eligibility(self):
        from app.domain.reforesta_profile import assess_reforesta_eligibility

        elig = assess_reforesta_eligibility(
            titulo=self.titulo_original or self.titulo_limpio,
            organo=self.organo_convocante,
            texto=self.resumen or "",
            beneficiarios_hint="",
            tipo_oportunidad=self.tipo_oportunidad,
            nivel_territorial=self.nivel_territorial,
            ccaa_codigo=self.ccaa_codigo,
            ccaa_nombre=self.ccaa_nombre,
            requisitos_resumen=self.requisitos_resumen or "",
            codigo_oficial=self.codigo_oficial,
            justificacion_juez=self.justificacion_juez or "",
        )
        stored_types = self.beneficiarios_tipos or []
        # Preserve ingestion-verified NGO eligibility from deep PDF/full text when no conflicting ban exists
        if (
            not elig.elegible
            and "ONG_FUNDACIONES" in stored_types
            and elig.beneficiarios_tipos == ["NO_ESPECIFICADO"]
            and not any(
                any(k in db.lower() for k in ("domicilio", "excluyen", "licitación", "reservada"))
                for db in (self.dealbreakers or [])
            )
        ):
            from app.domain.reforesta_profile import ReforestaEligibility

            elig = ReforestaEligibility(
                elegible=True,
                beneficiarios_tipos=stored_types,
                motivo_elegibilidad=(
                    f"Apta para Asociación Reforesta ({', '.join(stored_types)}). {self.justificacion_juez}"
                ).strip(),
                dealbreakers=[],
            )
        merged_dealbreakers = list(dict.fromkeys([*(elig.dealbreakers or []), *(self.dealbreakers or [])]))
        return elig, merged_dealbreakers

    def _default_matching_lineas(self) -> dict[str, int]:
        cats = set(self.categorias or [])
        restauracion = min(
            99,
            self.relevancia_score + (6 if cats & {"reforestacion", "restauracion_post_incendio", "restauracion_ecologica"} else -5),
        )
        conservacion = min(
            98,
            self.relevancia_score + (5 if cats & {"biodiversidad", "silvicultura", "prevencion_incendios"} else -4),
        )
        educacion = min(
            92,
            max(45, self.relevancia_score - (8 if "investigacion_forestal" not in cats else 0)),
        )
        return {
            "restauracionEcosistemas": max(40, restauracion),
            "conservacionHabitats": max(40, conservacion),
            "educacionAmbiental": max(35, educacion),
        }

    def to_frontend_convocatoria(self) -> dict[str, Any]:
        """
        Serialize directly to the TypeScript `Convocatoria` interface expected by
        Roi's Frontend (`origin/front:frontend/src/types/convocatoria.ts`).
        """
        tipo_fuente_map = {
            "UE": "europea",
            "ESTADO": "publica_estatal",
            "PRIVADA": "privada_rsc",
            "CCAA": "publica_autonomica",
            "PROVINCIA": "publica_autonomica",
            "MUNICIPIO": "publica_autonomica",
        }
        if (
            self.nivel_territorial == "PRIVADA"
            or self.tipo_oportunidad == "CONVOCATORIA_PRIVADA"
            or self.fuente == "FUNDACION_PRIVADA"
        ):
            tipo_fuente = "privada_rsc"
        else:
            tipo_fuente = tipo_fuente_map.get(self.nivel_territorial, "publica_autonomica")

        dias = self.dias_restantes if self.dias_restantes is not None else 0
        if dias <= 12:
            urgencia = "critica"
        elif dias <= 30:
            urgencia = "moderada"
        else:
            urgencia = "holgada"

        fin_pct = self.porcentaje_max_financiacion if self.porcentaje_max_financiacion is not None else 80.0
        porcentaje_cofinanciacion = max(0, round(100.0 - fin_pct))

        presupuesto = int(self.presupuesto_total or 0)
        raw_proy = int(self.importe_max_proyecto or 0)
        if self.importe_max_beneficiario:
            cuantia_max = int(self.importe_max_beneficiario)
        elif raw_proy > 0:
            # EU consortium calls (Horizon Europe RIA/IA) publish full multi-partner consortium totals (3M-12M EUR).
            # Cap single-NGO partner grant to a realistic tranche (max 350k EUR) so map & forecast totals remain realistic.
            if (
                self.tipo_oportunidad == "PROGRAMA_UE" or str(self.id).startswith("eu-")
            ) and raw_proy >= 1_000_000:
                cuantia_max = min(int(round(raw_proy * 0.05)), 350_000)
            else:
                cuantia_max = raw_proy
        elif presupuesto > 0:
            cuantia_max = min(presupuesto, 120_000)
        else:
            cuantia_max = 0

        elig, merged_dealbreakers = self._evaluate_reforesta_eligibility()
        elegible = elig.elegible
        motivo_elegibilidad = elig.motivo_elegibilidad

        acciones = [
            s.strip()
            for s in (self.gastos_subvencionables or "Reforestación con especies autóctonas, silvicultura preventiva y restauración de hábitats").split(",")
            if s.strip()
        ]
        requisitos_list = [
            s.strip()
            for s in (self.requisitos_resumen or "Asociación sin ánimo de lucro inscrita y al corriente de obligaciones tributarias").split(".")
            if s.strip()
        ]

        from app.domain.reforesta_profile import match_statute_alignment
        from app.pipeline.metadata_extractor import build_frontend_metadata_bundle

        est_align = match_statute_alignment(
            titulo=self.titulo_limpio,
            texto=f"{self.resumen} {self.gastos_subvencionables or ''}",
            categorias=self.categorias,
            ccaa_codigo=self.ccaa_codigo,
        )
        citas = list(
            self.citas_bases
            or [
                f"[{self.codigo_oficial}] {self.justificacion_juez}",
                f"[Plazo Oficial] {self.plazo_texto_original or 'Según bases reguladoras'}",
            ]
        )
        statute_cita = (
            f"[Estatutos Reforesta] {' · '.join(est_align['fines_alineados'][:2])} "
            f"({est_align['elegibilidad_juridica']})"
        )
        if not any("[Estatutos Reforesta]" in c for c in citas):
            citas.append(statute_cita)
        if est_align["presencia_territorial_previa"] and not any("[Presencia Reforesta]" in c for c in citas):
            citas.append(f"[Presencia Reforesta] {est_align['presencia_territorial_previa']}")

        def _pick_specific_doc_url(*candidates: str | None) -> str:
            urls = [u.strip() for u in candidates if u and u.strip()]
            for u in urls:
                low = u.lower()
                if (
                    ".pdf" in low
                    or "iddocumento=" in low
                    or "getdocumentbyid" in low
                    or "/api/v1/fuentes/" in low
                    or "descargararchivo" in low
                ):
                    return u
            for u in urls:
                low = u.lower()
                if any(tok in low for tok in ("documentid=", "verobj", "referencia=", "txt.php?id=", "/eli/", "topic-details/", "/convocatoria/", "convocatorias/")):
                    return u
            return urls[0] if urls else ""

        front_meta = build_frontend_metadata_bundle(self)
        ccaa_geojson_map = {
            "ES-AN": "Andalucía",
            "ES-AR": "Aragón",
            "ES-AS": "Principado de Asturias",
            "ES-IB": "Illes Balears",
            "ES-CN": "Canarias",
            "ES-CB": "Cantabria",
            "ES-CM": "Castilla-La Mancha",
            "ES-CL": "Castilla y León",
            "ES-CT": "Cataluña",
            "ES-VC": "Comunitat Valenciana",
            "ES-EX": "Extremadura",
            "ES-GA": "Galicia",
            "ES-RI": "La Rioja",
            "ES-MD": "Comunidad de Madrid",
            "ES-MC": "Región de Murcia",
            "ES-NC": "Navarra",
            "ES-PV": "País Vasco",
            "ES-CE": "Ceuta",
            "ES-ML": "Melilla",
            "ES": "Estatal",
            "EU": "Estatal",
        }
        base_ccaa = ccaa_geojson_map.get(self.ccaa_codigo or "ES", self.ccaa_nombre or "Estatal")
        sub_loc = self.municipio_nombre or self.provincia_nombre
        if base_ccaa == "Estatal":
            ambito_territorial = "Estatal"
        elif sub_loc and sub_loc.lower() not in base_ccaa.lower():
            ambito_territorial = f"{base_ccaa} · {sub_loc}"
        else:
            ambito_territorial = base_ccaa

        return {
            "id": self.id,
            "codigoOficial": self.codigo_oficial,
            "titulo": self.titulo_limpio,
            "tituloOriginal": self.titulo_original or self.titulo_limpio,
            "organismo": self.organo_convocante,
            "tipoFuente": tipo_fuente,
            "ambitoTerritorial": ambito_territorial,
            "ccaaCodigo": self.ccaa_codigo,
            "nivelTerritorial": self.nivel_territorial,
            "estado": self.estado,
            "anio": self.anio_convocatoria,
            "orografiaPendiente": self.orografia_pendiente,
            "presupuestoTotal": presupuesto,
            "cuantiaMaximaProyecto": cuantia_max,
            "porcentajeCofinanciacion": porcentaje_cofinanciacion,
            "modalidadPago": self.modalidad_pago or "mixto",
            "pagoAnticipadoSinAval": self.pago_anticipado_sin_aval,
            "fechaPublicacion": self.fecha_publicacion.isoformat() if self.fecha_publicacion else f"{self.anio_convocatoria}-01-15",
            "fechaCierre": self.fecha_fin_solicitud.isoformat() if self.fecha_fin_solicitud else f"{self.anio_convocatoria}-12-31",
            "diasRestantes": max(0, dias),
            "diasHabilesRestantes": front_meta["plazos"]["dias_habiles_restantes"],
            "urgencia": urgencia,
            "ubicacion": front_meta["ubicacion"],
            "plazos": front_meta["plazos"],
            "dinero": front_meta["dinero"],
            "elegible": elegible,
            "motivoElegibilidad": motivo_elegibilidad,
            "dealbreakers": merged_dealbreakers,
            "matchingGlobal": self.prioridad_score or self.relevancia_score,
            "matchingLineas": self.matching_lineas or self._default_matching_lineas(),
            "citasBasesJustificacion": citas,
            "resumenEjecutivo": self.resumen,
            "accionesSubvencionables": acciones[:5],
            "gastosNoSubvencionables": [
                "IVA recuperable o impuestos indirectos equivalentes",
                "Gastos financieros, intereses deudores o sanciones administrativas",
            ],
            "requisitosSolvencia": requisitos_list[:4],
            "urlBasesPdf": _pick_specific_doc_url(
                self.url_bases_reguladoras,
                self.url_boletin_extracto,
                self.url_ficha_oficial,
            ),
            "urlSedeElectronica": self.url_tramitacion or self.url_ficha_oficial,
            "fuenteUrl": self.url_ficha_oficial,
            "estadoInterno": self.estado_interno or ("priorizada" if (self.prioridad_score or 0) >= 85 else "nueva"),
        }


class UpdateEstadoInternoRequest(BaseModel):
    """Request schema to update an opportunity's internal workflow state."""

    estadoInterno: str = PydanticField(
        ...,
        description="nueva | priorizada | en_preparacion | presentada | descartada",
    )


class LLMVerdictCache(SQLModel, table=True):
    """Persistent Layer 2 verdict cache keyed by normalized content hash (SQLite / PostgreSQL)."""

    __tablename__ = "llm_verdict_cache"

    text_hash: str = Field(primary_key=True, index=True)
    metodo_evaluacion: str = Field(default="HYBRID_HEURISTIC")
    verdict_json: str = Field(sa_column=Column(Text))
    hit_count: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestionRun(SQLModel, table=True):
    """Audit log of ingestion runs across sources."""

    __tablename__ = "ingestion_runs"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = Field(default=None)
    sources: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    total_scanned: int = Field(default=0)
    passed_layer1: int = Field(default=0)
    accepted_layer2: int = Field(default=0)
    upserted_db: int = Field(default=0)
    status: str = Field(default="RUNNING")
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class AnalyzeTextRequest(BaseModel):
    """Request schema to evaluate arbitrary call text through the Hybrid Pipeline."""

    titulo: str = PydanticField(..., description="Título de la convocatoria o licitación")
    organo_convocante: str = PydanticField(default="", description="Ministerio, Consejería, Diputación, Ayuntamiento o Agencia UE")
    texto: str = PydanticField(..., description="Texto del extracto, bases u objeto de la convocatoria")
    fecha_publicacion: date | None = PydanticField(default=None)
    plazo_texto: str | None = PydanticField(default=None)
    presupuesto_total: float | None = PydanticField(default=None)
    url_oficial: str = PydanticField(default="")
    guardar_en_bd: bool = PydanticField(default=False)
