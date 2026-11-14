# 1hack_reforesta — Radar Vivo para Encontrar y Priorizar Oportunidades de Reforestación e Incendios

> **Propósito central:** *No redacta la propuesta. Reforesta ya sabe escribir; lo que le falta es capacidad para **encontrar** y **priorizar**.*

Plataforma de inteligencia en tiempo real diseñada para **capturar el 100% de las subvenciones, ayudas públicas, licitaciones, programas europeos y convocatorias privadas/RSC** de **reforestación, gestión forestal sostenible, restauración ecológica y prevención/extinción de incendios forestales** en España (`2020–2026`), y **priorizar automáticamente** dónde presentarse primero.

- **Plan Maestro del Proyecto**: [PLAN_PROYECTO.md](./PLAN_PROYECTO.md)
- **Rama Backend (`back`)**: Python + FastAPI + SQLModel (PostgreSQL Cloud / SQLite WAL Mode) + Motor de Priorización Táctica + Pipeline Híbrido Multilingüe (`ES`, `CA`, `GL`, `EU`, `EN`) + Extractor PDF (`PyMuPDF`).

---

## 1. Cómo Resuelve el Reto: Encontrar (100% Cobertura) + Priorizar (Scoring Táctico)

### A. Encontrar (Ingesta Multinivel en 6 Capas + Filtro Híbrido)
1. **Capa 1 — Filtro Rígido Multilingüe (`< 5 ms`, Coste 0)** ([layer1_regex.py](./app/pipeline/layer1_regex.py)):
   - Expresiones regulares ponderadas de alto recall en **castellano, catalán, gallego, euskera e inglés** (silvicultura, riberas, infraestructura verde urbana, mosaico agroforestal, prevención de incendios, captura de carbono, educación/voluntariado ambiental y soluciones basadas en la naturaleza).
   - Filtrado por códigos **CPV en dos niveles** (`Tier A`: `772*`, `75251120`, `034*`, `03121*`; `Tier B`: `9071*`, `9072*`, `7731*`, `7734*`, `451127*`, `71313*`, `7311*`) extraídos tanto de APIs/CODICE como de textos PDF.
   - Conectores en vivo y monitores web concurrentes ([live_connectors.py](./app/ingestors/live_connectors.py), [web_monitors.py](./app/ingestors/web_monitors.py)): BDNS (16 términos), BOE, PLACSP Atom (`sindicacion_643` + `sindicacion_1044`), RSS/Atom/HTML de las **19 CCAA**, monitores HTML para **Fundaciones Privadas/RSC** (*la Caixa, Motor Verde Repsol, Santander, BBVA, Biodiversidad, Iberdrola, Endesa, Afundación, EOCA, One Tree Planted*) y UE `SEDIA`.
   - **Seguimiento Extracto → PDF Completo + OCR Scanned Fallback**: Enriquecimiento automático desde el PDF oficial enlazado (`enrich_candidates_with_linked_pdfs`) y respaldo OCR en PDFs escaneados sin texto seleccionable ([pdf_extractor.py](./app/pipeline/pdf_extractor.py)).
   - **Ampliaciones de Plazo, Correcciones y Deduplicación Semántica** ([orchestrator.py](./app/pipeline/orchestrator.py)): Detección automática de *Ampliación de plazo* y *Corrección de errores* para actualizar in-situ el registro vivo, más deduplicación cruzada normativa (`BDNS`/`Orden`) y semántica (trigramas + similitud difusa).
   - Regla anti-trampa BDNS: **jamás descarta por el sector económico CNAE** de la ficha oficial (en [miteco-convocatoria-923290.pdf](./fuentes/miteco-convocatoria-923290.pdf) una ayuda ambiental de 17,38 M€ del MITECO figura etiquetada como *"Actividades Inmobiliarias"*).
   - Reglas anti-ruido que descartan falsos positivos (*extintores de hospitales, extinción de condominio, césped artificial, seguros de incendios domésticos*, etc.).
2. **Capa 2 — LLM Juez + Traductor al Español + Caché Persistente SQL** ([layer2_judge.py](./app/pipeline/layer2_judge.py)):
   - Clasifica cada oportunidad en **`DIRECTA`** (100% reforestación/silvicultura/incendios) o **`INDIRECTA_ELEGIBLE`** (convocatorias ambientales/biodiversidad/Red Natura 2000/clima donde un proyecto de reforestación es financiable, como los 2 PDFs de `./fuentes/`).
   - **Caché doble nivel (RAM LRU + tabla SQLite/PostgreSQL `llm_verdict_cache`)** que sobrevive reinicios sin repetir llamadas ni cuota LLM.
   - Traduce siempre `titulo_limpio`, `resumen` y `justificacion` al español.

### B. Priorizar (Motor de Priorización Estratégica + Viabilidad de Tesorería + Ley 39/2015)
Cada convocatoria abierta recibe en [prioritizer.py](./app/pipeline/prioritizer.py) un **`priorizacion.score` (`0–100`)** materializado e indexado en SQL (`ix_opp_estado_prioridad`) y un nivel (**`CRITICA` | `ALTA` | `MEDIA` | `BAJA`**) calculado sobre 4 ejes objetivos para decidir a qué presentarse hoy:
- **40% Afinidad Temática**: Peso directo a repoblación autóctona, restauración ecológica, custodia forestal y prevención/restauración de incendios, desglosado en 3 líneas (`restauracionEcosistemas`, `conservacionHabitats`, `educacionAmbiental`).
- **25% Elegibilidad para ONG / Asociación sin ánimo de lucro**: Prioriza convocatorias donde una entidad como Reforesta puede presentarse directamente (`ONG_FUNDACIONES`) o en alianza con `AYUNTAMIENTO` / `COMUNIDAD_MONTES`.
- **20% Intensidad Económica y Viabilidad de Tesorería**: Prioriza subvenciones que cubren del **80% al 100%** de los costes subvencionables, detecta **`modalidad_pago` (`anticipo` | `reembolso` | `mixto`)** y marca **`pago_anticipado_sin_aval`** (como el Art. 14 de la Orden 1689/2026 de la Comunidad de Madrid) frente a bloqueos de tesorería (`dealbreakers`).
- **15% Ventana de Oportunidad Temporal (Cumplimiento estricto Ley 39/2015 LPACAP Art. 30)**: Calcula los **días hábiles administrativos restantes** ([date_resolver.py](./app/pipeline/date_resolver.py)) descontando sábados, domingos, festivos nacionales, traslados de festivos en domingo y los **calendarios de festivos autonómicos de las 19 CCAA**, aplicando prórroga automática al primer día hábil siguiente cuando un plazo vence en inhábil (`Art. 30.5`) y cómputo *fecha a fecha* en plazos por meses (`Art. 30.4`).

### C. Anticipar y Exportar (Calendario Predictivo 2020–2026 + Exportadores Directos)
- **Calendario Predictivo de Recurrencia Anual (`GET /api/v1/opportunities/predictive-calendar`)** ([predictive_and_export.py](./app/pipeline/predictive_and_export.py)): Analiza el histórico `2020–2026` de convocatorias cíclicas (MITECO Línea A, Comunidad de Madrid Orden Ambiental ESAL, Fundación Biodiversidad, Programa LIFE, Motor Verde, Fundación ”la Caixa”, Xunta de Galicia, Junta de Andalucía) y alerta **45 días antes de su publicación en boletín** con el checklist técnico previo para no quedar fuera por plazos de solo 10 días hábiles.
- **Exportadores Directos sin Fricción**:
  - **Excel / Google Sheets CSV (`GET /api/v1/export/csv`)**: Con BOM UTF-8 (`\ufeff`) para abrir directamente en Excel con tildes y símbolos `€`.
  - **Calendario iCal RFC 5545 (`GET /api/v1/export/calendar.ics`)**: Eventos de cierre con alarmas automáticas `VALARM` a **7 días (`-P7D`)** y **48 horas (`-P2D`)** para Google Calendar, Outlook o Apple Calendar.
  - **Dossier Técnico Markdown (`GET /api/v1/export/markdown/{id}`)**: Ficha ejecutiva lista para el equipo técnico de Reforesta con cuadro financiero, citas de las bases y criterios de puntuación.

---

## 2. Catálogo Exhaustivo de Fuentes con Enlaces Oficiales

### 2.1. Fuentes Principales de Partida (Benchmark y Portales Clave)
- **Base de Datos Nacional de Subvenciones (BDNS / SNPSAP — Buscador y API)**: [infosubvenciones.es](https://www.infosubvenciones.es/) · [Portal API BDNS Hacienda](https://www.pap.hacienda.gob.es/bdnstrans/ge/es/convocatorias)
- **Boletines Oficiales de Referencia**: [BOE](https://www.boe.es/) · [BOCM (Madrid)](https://www.bocm.es/) · [DOG (Galicia)](https://www.xunta.gal/diario-oficial-galicia)
- **Organismos Estatales y Europeos Clave**: [Fundación Biodiversidad](https://www.fundacion-biodiversidad.es/) · [MITECO](https://www.miteco.gob.es/) · [Programa LIFE (CINEA)](https://cinea.ec.europa.eu/life_en) · [Funding & Tenders Portal de la UE](https://funding-and-tenders-portal.ec.europa.eu/)
- **Contratación Pública (Licitaciones Forestales y Prevención de Incendios)**: [Plataforma de Contratación del Sector Público (PLACSP)](https://contrataciondelestado.es/) · [BOE Datos Abiertos API](https://www.boe.es/datosabiertos/)

---

### 2.2. Programas de la Comisión Europea Aplicables a Territorio Español (`UE`)
| Programa Europeo | Ámbito / Enfoque Forestal e Incendios | Enlace Oficial |
| :--- | :--- | :--- |
| **EU Funding & Tenders Portal (SEDIA API)** | Buscador y API central de convocatorias de gestión directa de la UE | [funding-and-tenders-portal.ec.europa.eu](https://funding-and-tenders-portal.ec.europa.eu/) |
| **Programa LIFE (CINEA)** | Subprogramas *Nature & Biodiversity* y *Climate Change Mitigation & Adaptation* | [cinea.ec.europa.eu/life_en](https://cinea.ec.europa.eu/life_en) |
| **Horizon Europe (Cluster 6 & Mission Soil)** | I+D+i en ecosistemas forestales, prevención de megaincendios y restauración de suelos | [ec.europa.eu/horizon-europe](https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/horizon) |
| **Interreg VI-A España-Portugal (POCTEP)** | Cooperación transfronteriza hispano-lusa contra incendios forestales y reforestación | [poctep.eu](https://www.poctep.eu/) |
| **Interreg SUDOE (Sudoeste Europeo)** | Prevención de incendios, gestión forestal conjunta en España, Francia y Portugal | [interreg-sudoe.eu](https://interreg-sudoe.eu/) |
| **Interreg POCTEFA (Pirineos)** | Adaptación climática y gestión de bosques pirenaicos | [poctefa.eu](https://www.poctefa.eu/) |
| **Interreg Euro-MED** | Resiliencia de bosques mediterráneos frente al cambio climático | [interreg-euro-med.eu](https://interreg-euro-med.eu/) |
| **TED (Tenders Electronic Daily)** | Suplemento del Diario Oficial de la UE para licitaciones forestales europeas | [ted.europa.eu](https://ted.europa.eu/es/) |

---

### 2.3. Los 19 Boletines Oficiales de Comunidades y Ciudades Autónomas (`CCAA`)
| Código ISO | Comunidad / Ciudad Autónoma | Boletín Oficial | Enlace Oficial |
| :--- | :--- | :--- | :--- |
| `ES-AN` | **Andalucía** | BOJA — Boletín Oficial de la Junta de Andalucía | [juntadeandalucia.es/eboja.html](https://www.juntadeandalucia.es/eboja.html) |
| `ES-AR` | **Aragón** | BOA — Boletín Oficial de Aragón | [boa.aragon.es](https://www.boa.aragon.es/) |
| `ES-AS` | **Principado de Asturias** | BOPA — Boletín Oficial del Principado de Asturias | [sede.asturias.es/bopa](https://sede.asturias.es/bopa) |
| `ES-CB` | **Cantabria** | BOC — Boletín Oficial de Cantabria | [boc.cantabria.es](https://boc.cantabria.es/) |
| `ES-CE` | **Ceuta** | BOCCE — Boletín Oficial de la Ciudad de Ceuta | [ceuta.es/ceuta/bocce](https://www.ceuta.es/ceuta/bocce) |
| `ES-CL` | **Castilla y León** | BOCYL — Boletín Oficial de Castilla y León | [bocyl.jcyl.es](https://bocyl.jcyl.es/) |
| `ES-CM` | **Castilla-La Mancha** | DOCM — Diario Oficial de Castilla-La Mancha | [docm.jccm.es](https://docm.jccm.es/) |
| `ES-CN` | **Canarias** | BOC — Boletín Oficial de Canarias | [gobiernodecanarias.org/boc](https://www.gobiernodecanarias.org/boc/) |
| `ES-CT` | **Cataluña** | DOGC — Diari Oficial de la Generalitat de Catalunya | [dogc.gencat.cat](https://dogc.gencat.cat/) |
| `ES-EX` | **Extremadura** | DOE — Diario Oficial de Extremadura | [doe.juntaex.es](https://doe.juntaex.es/) |
| `ES-GA` | **Galicia** | DOG — Diario Oficial de Galicia | [xunta.gal/diario-oficial-galicia](https://www.xunta.gal/diario-oficial-galicia) |
| `ES-IB` | **Illes Balears** | BOIB — Butlletí Oficial de les Illes Balears | [caib.es/eboibfront](https://www.caib.es/eboibfront/) |
| `ES-MC` | **Región de Murcia** | BORM — Boletín Oficial de la Región de Murcia | [borm.es](https://www.borm.es/) |
| `ES-MD` | **Comunidad de Madrid** | BOCM — Boletín Oficial de la Comunidad de Madrid | [bocm.es](https://www.bocm.es/) |
| `ES-ML` | **Melilla** | BOME — Boletín Oficial de la Ciudad de Melilla | [bomemelilla.es](https://bomemelilla.es/) |
| `ES-NC` | **Comunidad Foral de Navarra** | BON — Boletín Oficial de Navarra | [bon.navarra.es](https://bon.navarra.es/) |
| `ES-PV` | **País Vasco / Euskadi** | BOPV / EHAA — Boletín Oficial del País Vasco | [euskadi.eus/bopv](https://www.euskadi.eus/bopv/) |
| `ES-RI` | **La Rioja** | BOR — Boletín Oficial de La Rioja | [web.larioja.org/bor-portada](https://web.larioja.org/bor-portada) |
| `ES-VC` | **Comunitat Valenciana** | DOGV — Diari Oficial de la Generalitat Valenciana | [dogv.gva.es](https://dogv.gva.es/) |

---

### 2.4. Las 50 Provincias: Boletines Oficiales Provinciales (BOPs), Diputaciones, Cabildos y Consells (`PROVINCIA`)
*(Todas las convocatorias provinciales y locales se capturan además de forma centralizada por ley vía [infosubvenciones.es](https://www.infosubvenciones.es/) y [PLACSP](https://contrataciondelestado.es/)).*

| Provincia | CCAA | Boletín Oficial Provincial / Diputación / Cabildo / Consell | Enlace Oficial |
| :--- | :--- | :--- | :--- |
| **Álava / Araba** | `ES-PV` | BOTHA — Boletín Oficial del Territorio Histórico de Álava (Arabako Foru Aldundia) | [araba.eus/botha](https://www.araba.eus/botha/) |
| **Albacete** | `ES-CM` | BOP de Albacete — Diputación Provincial de Albacete | [dipualba.es/bop](https://www.dipualba.es/bop/) |
| **Alicante / Alacant** | `ES-VC` | BOP de Alicante — Diputación de Alicante | [bop.dipgra.es / dip-alicante.es](https://www.dip-alicante.es/bop/) |
| **Almería** | `ES-AN` | BOP de Almería — Diputación de Almería | [dipalme.org](https://app.dipalme.org/pandora/) |
| **Asturias** | `ES-AS` | BOPA (Uniprovincial) — Principado de Asturias | [sede.asturias.es/bopa](https://sede.asturias.es/bopa) |
| **Ávila** | `ES-CL` | BOP de Ávila — Diputación Provincial de Ávila | [bop.diputacionavila.es](https://bop.diputacionavila.es/) |
| **Badajoz** | `ES-EX` | BOP de Badajoz — Diputación de Badajoz | [dip-badajoz.es/bop](https://www.dip-badajoz.es/bop/) |
| **Barcelona** | `ES-CT` | BOPB — Diputació de Barcelona | [bop.diba.cat](https://bop.diba.cat/) |
| **Bizkaia** | `ES-PV` | BOB — Boletín Oficial de Bizkaia (Bizkaiko Foru Aldundia) | [ebizkaia.eus/es/boletin-oficial-de-bizkaia](https://www.ebizkaia.eus/es/boletin-oficial-de-bizkaia) |
| **Burgos** | `ES-CL` | BOP de Burgos — Diputación Provincial de Burgos | [bopbur.diputaciondeburgos.es](https://bopbur.diputaciondeburgos.es/) |
| **Cáceres** | `ES-EX` | BOP de Cáceres — Diputación Provincial de Cáceres | [bop.dip-caceres.es](https://bop.dip-caceres.es/) |
| **Cádiz** | `ES-AN` | BOP de Cádiz — Diputación de Cádiz | [bopcadiz.es](https://www.bopcadiz.es/) |
| **Cantabria** | `ES-CB` | BOC (Uniprovincial) — Gobierno de Cantabria | [boc.cantabria.es](https://boc.cantabria.es/) |
| **Castellón / Castelló** | `ES-VC` | BOP de Castellón — Diputació de Castelló | [bop.dipcas.es](https://bop.dipcas.es/) |
| **Ciudad Real** | `ES-CM` | BOP de Ciudad Real — Diputación de Ciudad Real | [bop.dipucr.es](https://bop.dipucr.es/) |
| **Córdoba** | `ES-AN` | BOP de Córdoba — Diputación de Córdoba | [bop.dipucordoba.es](https://bop.dipucordoba.es/) |
| **A Coruña** | `ES-GA` | BOP da Coruña — Deputación Provincial da Coruña | [bop.dacoruna.gal](https://bop.dacoruna.gal/) |
| **Cuenca** | `ES-CM` | BOP de Cuenca — Diputación Provincial de Cuenca | [bop.dipucuenca.es](https://bop.dipucuenca.es/) |
| **Gipuzkoa** | `ES-PV` | BOG — Boletín Oficial de Gipuzkoa (Gipuzkoako Foru Aldundia) | [egoitza.gipuzkoa.eus/gao-bog](https://egoitza.gipuzkoa.eus/es/gao-bog) |
| **Girona** | `ES-CT` | BOP de Girona — Diputació de Girona | [ddgi.cat/bop](https://www.ddgi.cat/bop/) |
| **Granada** | `ES-AN` | BOP de Granada — Diputación de Granada | [bop2.dipgra.es](https://bop2.dipgra.es/) |
| **Guadalajara** | `ES-CM` | BOP de Guadalajara — Diputación de Guadalajara | [boletin.dguadalajara.es](https://boletin.dguadalajara.es/) |
| **Huelva** | `ES-AN` | BOP de Huelva — Diputación Provincial de Huelva | [sede.diphuelva.es](https://sede.diphuelva.es/servicios/boletin-oficial-de-la-provincia/) |
| **Huesca** | `ES-AR` | BOP de Huesca — Diputación Provincial de Huesca | [bop.dphuesca.es](https://bop.dphuesca.es/) |
| **Illes Balears** | `ES-IB` | BOIB & Consells Insulars (Mallorca, Menorca, Eivissa, Formentera) | [conselldemallorca.cat](https://web.conselldemallorca.cat/) |
| **Jaén** | `ES-AN` | BOP de Jaén — Diputación Provincial de Jaén | [bop.dipujaen.es](https://bop.dipujaen.es/) |
| **León** | `ES-CL` | BOP de León — Diputación Provincial de León | [dipuleon.es/bopSearch](https://www.dipuleon.es/bopSearch/) |
| **Lleida** | `ES-CT` | BOP de Lleida — Diputació de Lleida | [bop.diputaciolleida.cat](https://bop.diputaciolleida.cat/) |
| **Lugo** | `ES-GA` | BOP de Lugo — Deputación Provincial de Lugo | [deputacionlugo.gal/boletin-oficial-da-provincia-de-lugo](https://www.deputacionlugo.gal/gl/boletin-oficial-da-provincia-de-lugo) |
| **Madrid** | `ES-MD` | BOCM (Uniprovincial) — Comunidad de Madrid | [bocm.es](https://www.bocm.es/) |
| **Málaga** | `ES-AN` | BOP de Málaga — Diputación Provincial de Málaga | [bopmalaga.es](https://www.bopmalaga.es/) |
| **Murcia** | `ES-MC` | BORM (Uniprovincial) — Región de Murcia | [borm.es](https://www.borm.es/) |
| **Navarra** | `ES-NC` | BON (Uniprovincial) — Comunidad Foral de Navarra | [bon.navarra.es](https://bon.navarra.es/) |
| **Ourense** | `ES-GA` | BOP de Ourense — Deputación Provincial de Ourense | [bop.depourense.es](https://bop.depourense.es/) |
| **Palencia** | `ES-CL` | BOP de Palencia — Diputación Provincial de Palencia | [diputaciondepalencia.es/sitio/bop](https://www.diputaciondepalencia.es/sitio/bop) |
| **Las Palmas** | `ES-CN` | BOP de Las Palmas & Cabildos de Gran Canaria, Lanzarote y Fuerteventura | [boplaspalmas.net](https://www.boplaspalmas.net/) |
| **Pontevedra** | `ES-GA` | BOPPO — Deputación Provincial de Pontevedra | [boppo.depo.gal](https://boppo.depo.gal/) |
| **La Rioja** | `ES-RI` | BOR (Uniprovincial) — Gobierno de La Rioja | [web.larioja.org/bor-portada](https://web.larioja.org/bor-portada) |
| **Salamanca** | `ES-CL` | BOP de Salamanca — Diputación de Salamanca | [sede.diputaciondesalamanca.gob.es/bop](https://sede.diputaciondesalamanca.gob.es/bop/) |
| **Santa Cruz de Tenerife** | `ES-CN` | BOP de S/C de Tenerife & Cabildos de Tenerife, La Palma, La Gomera y El Hierro | [bopsantacruzdetenerife.es](https://www.bopsantacruzdetenerife.es/) |
| **Segovia** | `ES-CL` | BOP de Segovia — Diputación Provincial de Segovia | [dipsegovia.es/bop](https://www.dipsegovia.es/bop) |
| **Sevilla** | `ES-AN` | BOP de Sevilla — Diputación Provincial de Sevilla | [bopsevilla.dipusevilla.es](https://bopsevilla.dipusevilla.es/) |
| **Soria** | `ES-CL` | BOP de Soria — Diputación Provincial de Soria | [bop.dipsoria.es](https://bop.dipsoria.es/) |
| **Tarragona** | `ES-CT` | BOPT — Diputació de Tarragona | [dipta.cat/bopt](https://www.dipta.cat/bopt) |
| **Teruel** | `ES-AR` | BOP de Teruel — Diputación Provincial de Teruel | [dpteruel.es/BOPTe](https://www.dpteruel.es/BOPTe/) |
| **Toledo** | `ES-CM` | BOP de Toledo — Diputación Provincial de Toledo | [diputoledo.es/bop](https://www.diputoledo.es/) |
| **Valencia / València** | `ES-VC` | BOP de Valencia — Diputació de València | [bop.dival.es](https://bop.dival.es/) |
| **Valladolid** | `ES-CL` | BOP de Valladolid — Diputación de Valladolid | [bop.sede.diputaciondevalladolid.es](https://bop.sede.diputaciondevalladolid.es/) |
| **Zamora** | `ES-CL` | BOP de Zamora — Diputación Provincial de Zamora | [diputaciondezamora.es/bop](https://www.diputaciondezamora.es/) |
| **Zaragoza** | `ES-AR` | BOPZ — Diputación Provincial de Zaragoza | [bop.dpz.es](https://bop.dpz.es/) |

---

### 2.5. Municipios: Concellos, Ayuntamientos, Ajuntaments y Udalak (`MUNICIPIO`)
- **Agregador Legal Obligatorio de los 8.131 Municipios (Ley 38/2003, Art. 18 y 20)**: [BDNS / infosubvenciones.es](https://www.infosubvenciones.es/) y [PLACSP Contratación Local](https://contrataciondelestado.es/).
- **Federación Española de Municipios y Provincias (FEMP) — Red Española de Ciudades por el Clima / Bosques Urbanos**: [femp.es](https://www.femp.es/) · [redciudadesclima.es](https://www.redciudadesclima.es/)
- **Ejemplos de Portales Municipales y Forestales Activos en la Base de Datos**:
  - [Concello de Pontevedra](https://www.pontevedra.gal/) · [Concello de Lalín](https://www.lalin.gal/) · [Ayuntamiento de Soria (Monte Valonsadero / Bosque Modelo)](https://www.soria.es/) · [Ayuntamiento de Cangas del Narcea (Reserva Muniellos)](https://www.ayto-cangasdelnarcea.es/) · [Oñatiko Udala / Ayuntamiento de Oñati](https://www.onati.eus/) · [Ayuntamiento de Cuenca](https://www.cuenca.es/) · [Ayuntamiento de Madrid](https://sede.madrid.es/)

---

### 2.6. Fundaciones Privadas y Programas de RSC con Convocatoria Pública (`PRIVADA`)
| Entidad Privada / Programa RSC | Tipo de Ayuda / Convocatoria | Enlace Oficial |
| :--- | :--- | :--- |
| **Fundación ”la Caixa”** | Convocatoria de Medio Ambiente: Restauración de ecosistemas forestales y prevención de incendios | [fundacionlacaixa.org/es/convocatorias-medioambiente](https://fundacionlacaixa.org/es/convocatorias-medioambiente) |
| **Motor Verde (Fundación Repsol & Grupo Sylvestris)** | Financiación 100% para grandes proyectos de reforestación de montes quemados/baldíos y absorción de CO2 | [fundacionrepsol.com/es/motor-verde](https://www.fundacionrepsol.com/es/motor-verde/) |
| **Fundación Banco Santander** | Convocatorias de Recuperación de Patrimonio Natural y Bosques Autóctonos | [fundacionbancosantander.com/es/accion-sostenible](https://www.fundacionbancosantander.com/es/accion-sostenible) |
| **Fundación BBVA** | Ayudas a Proyectos de Investigación y Conservación en Ecología y Biología de la Conservación | [fbbva.es/ayudas](https://www.fbbva.es/ayudas/) |
| **Fundación Iberdrola España** | Programa de Biodiversidad, Plan Bosque Defensa y Restauración de Hábitats | [fundacioniberdrolaespana.org](https://www.fundacioniberdrolaespana.org/) |
| **Fundación Endesa** | Convocatorias de Proyectos de Biodiversidad, Renaturalización e Iluminación/Ecoeficiencia | [fundacionendesa.org/es/biodiversidad](https://www.fundacionendesa.org/es/biodiversidad) |
| **Fundación Naturgy** | Premios y Ayudas a Iniciativas Sociales y Ambientales / Transición Ecológica | [fundacionnaturgy.org](https://www.fundacionnaturgy.org/) |
| **Obra Social ABANCA / Afundación** | Programas RSC *Rebrote* y *PlanctON* de reforestación autóctona y montes vecinales | [afundacion.org](https://www.afundacion.org/) |
| **Fundación Caja de Burgos & Fundación Gutiérrez Manrique** | Convocatoria anual de Ayudas de Medio Ambiente, Bosques y Custodia del Territorio | [cajadeburgos.com](https://www.cajadeburgos.com/) |
| **Fundación CajaCanarias** | Convocatoria de Ayudas a Proyectos Medioambientales y Restauración Forestal Insular | [cajacanarias.com](https://www.cajacanarias.com/) |
| **Fundación Tatiana Pérez de Guzmán el Bueno** | Convocatoria de Ayudas a Proyectos de Medio Ambiente e Investigación Ambiental | [fundaciontatianapgb.org](https://fundaciontatianapgb.org/) |
| **EOCA (European Outdoor Conservation Association)** | *Conservation Grants* internacionales de RSC para proyectos de reforestación de ONGs | [outdoorconservation.eu](https://www.outdoorconservation.eu/) |
| **One Tree Planted & 1% for the Planet** | Financiación corporativa de RSC para plantación de árboles autóctonos con ONGs locales en España | [onetreeplanted.org](https://onetreeplanted.org/) |
| **Bosques Sostenibles & ReTree** | Proyectos de RSC corporativa para reforestación y Registro de Huella de Carbono MITECO | [bosquessostenibles.com](https://www.bosquessostenibles.com/) |

---

## 3. Arranque Rápido y Comandos

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Levantar servidor FastAPI (puerto 8000)
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000

# 3. Ejecutar suite completa de 68 tests (Golden Benchmark + Recall/Precision + Geo/LPACAP + Conectores/PDF/OCR + Mejoras 1-5 + E2E API)
.\.venv\Scripts\pytest -v
```

- **Swagger UI interactivo**: `http://localhost:8000/docs`

---

## 4. Contrato de Endpoints REST para el Frontend (`roialtra`)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/convocatorias` | **Puente Plug-and-Play Next.js (`roialtra`)**: Devuelve todas las oportunidades adaptadas exactamente a la interfaz TypeScript `Convocatoria` (`frontend/src/types/convocatoria.ts`). |
| `PATCH` | `/api/convocatorias/{id}/estado` | Actualiza el estado interno de trabajo de una convocatoria (`nueva` \| `priorizada` \| `en_preparacion` \| `presentada` \| `descartada`). |
| `GET` | `/api/v1/opportunities/prioritized` | **Cola de Priorización Inteligente para Reforesta**: Devuelve las oportunidades activas ordenadas por `priorizacion.score` (`CRITICA`, `ALTA`, `MEDIA`), filtrable por `ccaa`, `perfil_beneficiario=ONG_FUNDACIONES` y `solo_anticipo_sin_aval`. |
| `GET` | `/api/v1/opportunities/predictive-calendar` | **Calendario Predictivo de Recurrencia Anual (`2020–2026`)**: Predice meses de apertura, ventanas de preparación de 45 días y checklists técnicos para convocatorias cíclicas. |
| `GET` | `/api/v1/export/csv` | **Exportador directo a Excel / Google Sheets (`.csv` UTF-8-SIG)** con todas las oportunidades priorizadas y desglose financiero. |
| `GET` | `/api/v1/export/calendar.ics` | **Exportador directo a Google Calendar / Outlook (`.ics` RFC 5545)** con eventos de cierre y alarmas `VALARM` a 7 días y 48 horas. |
| `GET` | `/api/v1/export/markdown/{id}` | **Exportador de Ficha Técnica de Preparación (`.md`)** con cuadro de tesorería, citas literales de las bases, dealbreakers y criterios de valoración. |
| `GET` | `/api/v1/map/summary` | Resumen instantáneo por las **19 CCAA/Ciudades Autónomas** (`ES-AN`..`ES-VC`) + Estatal (`ES`) + Privadas/RSC (`PRIVADA`) + Europeo (`EU`) con desglose autonómico, provincial y de concellos/ayuntamientos. |
| `GET` | `/api/v1/opportunities` | Buscador y filtrado SQL indexado (`estado`, `ccaa`, `incluir_nacionales_ue`, `provincia`, `nivel`, `tipo`, `relevancia`, `categoria`, `beneficiario`, `modalidad_pago`, `solo_anticipo_sin_aval`, `anio`, `anio_desde`, `anio_hasta`, `presupuesto_min`, `cofinanciado_ue`, `q`, `sort_by=prioridad_score`). |
| `GET` | `/api/v1/opportunities/{id}` | Ficha completa de una oportunidad (incluye bloque `priorizacion`, importes individuales, viabilidad de tesorería, enlaces oficiales y criterios de valoración). |
| `GET` | `/api/v1/sources/registry` | Catálogo en vivo de las **fuentes oficiales y privadas/RSC** monitorizadas en los 6 niveles (`UE`, `ESTADO`, `CCAA`, `PROVINCIA`, `MUNICIPIO`, `PRIVADA`). |
| `GET` | `/api/v1/stats/historical` | Series temporales del **Histórico Profundo (`2020–2026`)**, desglose por nivel territorial/categoría y auditoría de ruido descartado. |
| `GET` | `/api/v1/benchmark/verify` | Verifica y devuelve las 2 convocatorias del Golden Benchmark (`bdns-923290` MITECO y `bocm-orden-1689-2026` Comunidad de Madrid). |
| `POST` | `/api/v1/ingest/trigger` | Lanza una sincronización concurrente en vivo (`asyncio.gather` protegida por `asyncio.Lock`) contra `./fuentes/`, BDNS, PLACSP Atom (`643`+`1044`), BOE, 19 CCAA (RSS/Atom/HTML), Fundaciones Privadas, enriquecimiento Extracto→PDF y UE SEDIA. |
| `POST` | `/api/v1/analyze/text` | Evalúa y prioriza cualquier texto de convocatoria en vivo pasando por Capa 1 + Capa 2 + Motor de Priorización. |
| `POST` | `/api/v1/analyze/pdf` | Sube un PDF de boletín oficial o ficha BDNS en vivo y devuelve el JSON estructurado y priorizado. |
