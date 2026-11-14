"""Database models and API response schemas for 1hack_reforesta."""
from datetime import date, datetime, timezone
from typing import Any
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import Field, SQLModel


class Opportunity(SQLModel, table=True):
    """Unified model for grants, subsidies, public tenders, EU calls and private funds (2020-2026)."""

    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opp_estado_ccaa", "estado", "ccaa_codigo"),
        Index("ix_opp_anio_estado", "anio_convocatoria", "estado"),
        Index("ix_opp_nivel_ccaa", "nivel_territorial", "ccaa_codigo"),
        Index("ix_opp_relevancia_estado", "relevancia_tipo", "estado"),
    )

    id: str = Field(primary_key=True, index=True)
    codigo_oficial: str = Field(index=True)
    fuente: str = Field(index=True)  # BDNS | PLACSP | BOE | EU_SEDIA | BOLETIN_CCAA | FUENTES_PDF
    tipo_oportunidad: str = Field(index=True)  # SUBVENCION | LICITACION | PROGRAMA_UE | CONVENIO
    estado: str = Field(index=True)  # ACTIVA | PROXIMA | CERRADA
    dias_restantes: int | None = Field(default=None, index=True)

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

    # Geography
    nivel_territorial: str = Field(index=True)  # UE | ESTADO | CCAA | PROVINCIA | MUNICIPIO
    ccaa_codigo: str = Field(index=True)  # ES-AN..ES-VC, ES, EU
    ccaa_nombre: str = Field(default="")
    provincia_codigo: str | None = Field(default=None, index=True)
    provincia_nombre: str | None = Field(default=None)
    municipio_nombre: str | None = Field(default=None)

    # Issuing Body
    organo_convocante: str = Field(default="", sa_column=Column(Text))
    unidad_convocante: str | None = Field(default=None)

    # Financials
    presupuesto_total: float | None = Field(default=None, index=True)
    importe_max_proyecto: float | None = Field(default=None)
    importe_max_beneficiario: float | None = Field(default=None)
    porcentaje_max_financiacion: float | None = Field(default=None)
    moneda: str = Field(default="EUR")
    cofinanciado_ue: bool = Field(default=False, index=True)
    fondo_ue: str | None = Field(default=None)

    # Beneficiaries & Requirements
    beneficiarios_tipos: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    sector_economico_original: str | None = Field(default=None)
    requisitos_resumen: str = Field(default="", sa_column=Column(Text))
    gastos_subvencionables: str | None = Field(default=None, sa_column=Column(Text))
    criterios_valoracion: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))

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
        from app.pipeline.prioritizer import calculate_priority

        prio = calculate_priority(
            estado=self.estado,
            dias_restantes=self.dias_restantes,
            relevancia_tipo=self.relevancia_tipo,
            relevancia_score=self.relevancia_score,
            beneficiarios_tipos=self.beneficiarios_tipos or [],
            porcentaje_financiacion=self.porcentaje_max_financiacion,
            presupuesto_total=self.presupuesto_total,
            importe_max_proyecto=self.importe_max_proyecto,
            nivel_territorial=self.nivel_territorial,
        )
        return {
            "id": self.id,
            "codigo_oficial": self.codigo_oficial,
            "tipo_oportunidad": self.tipo_oportunidad,
            "estado": self.estado,
            "dias_restantes": self.dias_restantes,
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
            },
            "titulo_limpio": self.titulo_limpio,
            "titulo_original": self.titulo_original,
            "resumen": self.resumen,
            "ambito_geografico": {
                "nivel": self.nivel_territorial,
                "ccaa_codigo": self.ccaa_codigo,
                "ccaa_nombre": self.ccaa_nombre,
                "provincia_codigo": self.provincia_codigo,
                "provincia_nombre": self.provincia_nombre,
                "municipio": self.municipio_nombre,
            },
            "organo_convocante": {
                "nivel_administracion": self.nivel_territorial,
                "administracion": self.organo_convocante,
                "unidad": self.unidad_convocante,
            },
            "economia": {
                "presupuesto_total": self.presupuesto_total,
                "importe_max_proyecto": self.importe_max_proyecto,
                "importe_max_beneficiario": self.importe_max_beneficiario,
                "porcentaje_max_financiacion": self.porcentaje_max_financiacion,
                "moneda": self.moneda,
                "cofinanciado_ue": self.cofinanciado_ue,
                "fondo_ue": self.fondo_ue,
            },
            "beneficiarios": {
                "tipos": self.beneficiarios_tipos or [],
                "descripcion_requisitos": self.requisitos_resumen,
                "gastos_subvencionables": self.gastos_subvencionables,
                "criterios_valoracion": self.criterios_valoracion or [],
            },
            "fechas": {
                "anio_convocatoria": self.anio_convocatoria,
                "fecha_publicacion": self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
                "fecha_inicio_solicitud": self.fecha_inicio_solicitud.isoformat() if self.fecha_inicio_solicitud else None,
                "fecha_fin_solicitud": self.fecha_fin_solicitud.isoformat() if self.fecha_fin_solicitud else None,
                "plazo_texto_original": self.plazo_texto_original,
                "es_plazo_calculado": self.es_plazo_calculado,
            },
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
