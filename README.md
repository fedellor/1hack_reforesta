# Radar Reforesta (`1hack_reforesta`)

> **Herramienta interna de captación y priorización de financiación** para **Asociación Reforesta** (ONG ambiental declarada de Utilidad Pública, CIF `G80428204`).
> **Rama actual:** `main` (producción consolidada Full-Stack).

Radar Reforesta automatiza la detección, el filtrado jurídico para ESAL y la priorización técnica/financiera de subvenciones públicas, licitaciones forestales, fondos europeos y convocatorias privadas de mecenazgo/RSC en España (**histórico real desde `2016` y convocatorias vigentes hacia `2027+`**, sin datos simulados).

---

## 1. Estructura y Propósito de las Ramas

| Rama | Rol | Contenido y Criterio de Uso |
| :--- | :--- | :--- |
| **`main`** | **Producción / Demo consolidada** | Código unificado Full-Stack listo para arrancar: backend validado (`app/`, `tests/`) + frontend completo (mapa y buscador de `test` junto con las vistas operativas de `front`). |
| **`test`** | **Integración y validación Full-Stack** | Rama puente donde se combinan las actualizaciones de `back` y `front`, se resuelven incompatibilidades de contrato y se ejecutan `pytest`, `tsc` y `next build` antes de fusionar a `main`. |
| **`back`** | **Desarrollo Backend (Python/FastAPI)** | API REST, conectores en vivo (`BDNS`, `BOE`, `PLACSP`, `19 CCAA`, `UE SEDIA`, fundaciones RSC), motor de elegibilidad ESAL y tests unitarios/E2E. |
| **`front`** | **Desarrollo Frontend (Next.js/React)** | Iteraciones de interfaz de usuario (`Plan de ataque`, `Previsión`, `Histórico`, `Empresas`, componentes y estilos corporativos de Reforesta). |

**Flujo de integración:** `back` + `front` → `test` *(se integra todo salvo sobreescribir el backend ni el mapa/buscador propios de `test`)* → `main`.

---

## 2. Capacidades Clave de la Plataforma

### Backend Inteligente (`app/`)
- **Cobertura multicanal real (`100%` fuentes reales, `include_catalog_templates=false`):**
  - **BDNS / SNPSAP**, **BOE Datos Abiertos**, **PLACSP Atom** (`sindicacion_643` + `sindicacion_1044`), **19 boletines autonómicos**, **UE Funding & Tenders (SEDIA)**, PDFs locales en `fuentes/` y monitores HTML dedicados a fundaciones/RSC (*Fundación ”la Caixa”*, *CajaCanarias*, *Fundación Biodiversidad*, *Motor Verde / Repsol*, *Santander*, *BBVA*, *Iberdrola*, *Endesa*, *Afundación*, *Caja de Burgos*, *EOCA*, etc.).
- **Filtro Híbrido Multilingüe (`ES`, `CA`, `GL`, `EU`, `EN`):**
  - **Capa 1 (`app/pipeline/layer1_regex.py`):** filtrado determinista de alta precisión (`TITLE_HARD_EXCLUSION_PATTERN` + `HARD_EXCLUSION_PATTERN`, códigos CPV forestales/ambientales, bloqueo de ruido doméstico/mercantil).
  - **Capa 2 (`app/pipeline/layer2_judge.py`):** clasificación asistida (Gemini / Groq / OpenRouter o motor determinista local sin clave externa) con caché persistente en SQL.
- **Motor estricto de Elegibilidad ESAL (`app/domain/reforesta_profile.py`):**
  - Distingue convocatorias **aptas** para Reforesta (asociación sin ánimo de lucro declarada de Utilidad Pública) de aquellas restringidas por título o bases a ayuntamientos, pymes/empresas mercantiles, explotaciones agrarias o personas físicas, exponiendo los *dealbreakers* detectados.
- **Horizonte histórico y sincronización diaria (`app/config.py`, `app/main.py`):**
  - Base SQLite WAL (`./data/reforesta.db`) o PostgreSQL desde **`2016`** hasta convocatorias vigentes con cierre en **`2027+`**.
  - Actualización automática diaria programada a las **`07:00` (`Europe/Madrid`)**, más disparo manual bajo demanda (`POST /api/v1/ingest/trigger`).
- **Cálculo administrativo de plazos (`app/pipeline/date_resolver.py`):**
  - Días hábiles restantes según **Ley 39/2015 LPACAP Art. 30** con calendarios nacionales y de las 19 CCAA.

### Frontend Ejecutivo (`frontend/`)
Identidad corporativa interna alineada con Reforesta (`#6aa43a`, Open Sans / Merriweather) organizada en cinco vistas operativas:
1. **Mapa (`MapView.tsx` + `LeafletMap.tsx` + `lib/search.ts`):** coropleta por CCAA sin teselas externas, embudo superior, buscador inteligente (soporta acrónimos como `MITECO`, `OAPN`, `PEPAC`, `PRTR`, `BDNS`, códigos numéricos y territorio) y panel por comunidad.
2. **Plan de ataque (`PlanView.tsx` + `ProgramaDrawer.tsx`):** priorización por cierre inminente, próximas aperturas y estado interno de preparación.
3. **Previsión (`PrevisionView.tsx` + `lib/recurrencia.ts`):** detección automática de programas anuales recurrentes a partir del histórico real `2016+` con ventana estimada de apertura y grado de fiabilidad.
4. **Histórico (`HistoricoView.tsx`):** archivo completo de convocatorias cerradas desde **`2016`**, gráfico interactivo por año, filtros territoriales y buscador inteligente.
5. **Empresas (`EmpresasView.tsx`):** canal específico de fundaciones y mecenazgo RSC (`privada_rsc`) con selector de elegibilidad, motivos de exclusión y archivo histórico privado.
6. **Ficha Ejecutiva (`ConvocatoriaDrawer.tsx`):** veredicto jurídico, financiación/anticipo, plazo hábil, citas de las bases, enlace directo al PDF/convocatoria específica y exportación a Markdown.

---

## 3. Estructura del Repositorio

```text
reforesta/
├── app/
│   ├── main.py                       # Servidor FastAPI, endpoints REST y scheduler 07:00 Europe/Madrid
│   ├── config.py                     # Configuración Pydantic (horizonte 2016+, DB, LLM, sync)
│   ├── database.py                   # Motor SQLModel (SQLite WAL / PostgreSQL)
│   ├── models.py                     # Esquemas ORM y serialización hacia frontend
│   ├── geo.py                        # Normalización territorial España (CCAA, provincias, PRIVADA, UE)
│   ├── search_utils.py               # Normalización de texto y matching de búsqueda
│   ├── domain/reforesta_profile.py   # Perfil estatutario Reforesta y detector ESAL / dealbreakers
│   ├── ingestors/                    # Conectores BDNS, BOE, PLACSP, CCAA, SEDIA y monitores RSC
│   └── pipeline/                     # Capa 1, Capa 2, PDF/OCR, fechas LPACAP, priorización y export
├── frontend/                         # Aplicación Next.js 16 + React 19 + Tailwind CSS v4 + Leaflet
├── fuentes/                          # Documentos PDF de referencia (benchmark MITECO y CAM)
├── tests/                            # Suite pytest (pipeline, conectores, geo, búsqueda y API)
├── .env.example                      # Variables de entorno recomendadas
├── requirements.txt                  # Dependencias Python
├── PLAN_PROYECTO.md                  # Diseño técnico del backend
└── REQUERIMIENTOS.md                 # Contrato funcional y de datos
```

---

## 4. Puesta en Marcha en Local

### Requisitos
- **Python 3.11+** con entorno virtual en `.venv`
- **Node.js 18+** y **npm**

### 1. Backend (`:8000`)
```powershell
# Crear/activar entorno virtual e instalar dependencias (primera vez)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Opcional: copiar variables de entorno
Copy-Item .env.example .env

# Ejecutar batería de tests
.\.venv\Scripts\pytest.exe -v

# Arrancar API FastAPI en puerto 8000
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```
- Documentación interactiva OpenAPI/Swagger: `http://localhost:8000/docs`
- Inspector operativo del radar: `http://localhost:8000/radar`

### 2. Frontend (`:3000`)
> En Windows con políticas restrictivas de PowerShell, usar **`npm.cmd`** en lugar de `npm`.

```powershell
cd frontend
npm.cmd install

# Verificación de tipos + compilación de producción
.\node_modules\.bin\tsc.cmd --noEmit
npm.cmd run build

# Arrancar servidor en producción (o `npm.cmd run dev` en desarrollo)
npm.cmd run start
```
- Aplicación web interna: `http://localhost:3000`

---

## 5. Endpoints REST Principales

| Método | Ruta | Uso |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Estado del servicio, base de datos y próxima sincronización |
| `GET` | `/api/convocatorias` | Catálogo adaptado al contrato `Convocatoria` del frontend (`estado=ACTIVA\|TODAS`) |
| `PATCH` | `/api/convocatorias/{id}/estado` | Cambio de estado interno en el flujo de trabajo |
| `GET` | `/api/v1/map/summary` | Agregados territoriales por CCAA, Estatal, Europea y Privada/RSC |
| `GET` | `/api/v1/stats/historical` | Estadísticas históricas desde 2016 y auditoría de fuentes |
| `GET` | `/api/v1/opportunities/prioritized` | Cola priorizada con filtros por CCAA, beneficiario y anticipo |
| `GET` | `/api/v1/opportunities/predictive-calendar` | Recurrencias anuales detectadas desde el histórico |
| `GET` | `/api/v1/sources/registry` | Registro de fuentes monitorizadas y estado de conectores |
| `GET` | `/api/v1/export/csv` \| `/calendar.ics` \| `/markdown/{id}` | Exportación a Excel, calendario iCal (RFC 5545) y dossier Markdown |
| `POST` | `/api/v1/ingest/trigger` | Ejecución manual del pipeline completo de ingesta y reevaluación |
| `POST` | `/api/v1/analyze/text` \| `/analyze/pdf` | Análisis puntual de textos o bases PDF |
