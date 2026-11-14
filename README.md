# Radar Reforesta

Herramienta **interna** de **Asociación Reforesta** (ONG ambiental declarada de Utilidad Pública, CIF `G80428204`) para encontrar, filtrar y priorizar financiación para reforestación y gestión forestal en España: subvenciones públicas, licitaciones, programas europeos y mecenazgo de fundaciones y empresas.

Hace tres cosas que hoy se hacen a mano:

1. **Buscar más allá de las fuentes habituales.** Rastrea cada día BDNS, BOE, TED/PLACSP, la UE (SEDIA), 19 boletines autonómicos y fundaciones.
2. **Evitar leer decenas de páginas de bases.** Cada convocatoria llega con un veredicto de elegibilidad para Reforesta (según sus estatutos), los requisitos que la excluyen y las citas de las bases que lo justifican.
3. **Anticiparse.** A partir del histórico detecta los programas que se repiten cada año y estima cuándo volverán a abrir.

Todo el contenido sale de fuentes reales: no hay datos de ejemplo. Si el backend no responde, la web lo dice en lugar de mostrar datos inventados.

---

## Qué se ve en la web

| Sección | Para qué sirve |
| :--- | :--- |
| **Mapa** | Reparto territorial de la financiación abierta, con buscador (acepta `MITECO`, `BDNS`, códigos o territorio), filtro de aptas/excluidas y panel por comunidad. |
| **Plan de ataque** | Pensado para la urgencia: eliges un mes y ves qué convocatorias abiertas cierran, con una barra por convocatoria hasta su fecha de cierre. Las confirmadas que aún no han abierto se avisan en el mes en que abren. |
| **Empresas** | Fundaciones y empresas que financian proyectos (mecenazgo/RSC). |
| **Previsión** | Qué suele salir el mes que viene según el histórico, agrupado por organismo, con un gráfico de los próximos 12 meses y la **medición de acierto** de la propia previsión. |
| **Histórico** | Archivo de convocatorias cerradas desde 2020 con buscador y filtros (año, territorio, tipo, solo aptas, se repiten). |
| **Ficha** | Al pulsar cualquier convocatoria: elegibilidad, importe, cierre, afinidad, citas de las bases y el botón **Convocatoria oficial**. |

Decisiones que conviene conocer:

- Las **licitaciones** (TED/PLACSP) se muestran, pero su importe es el del contrato y **no suma como fondos** en el mapa ni en los totales. Se reconocen por el identificador (`ted-…`, `placsp-…`).
- La **Previsión** solo incluye programas en los que alguna edición anterior fue apta para Reforesta. La ventana de apertura es de 3 meses como máximo. Los porcentajes de acierto se calculan con el histórico cargado y se recalculan solos al sincronizar más datos; son proporciones reales sobre pocos casos, no garantías.
- Los datos que el backend rellena por defecto (cofinanciación, modalidad de pago, orografía) **no se muestran** porque no son fiables.

---

## Arranque rápido con Docker

Requisitos: Docker con Compose. En macOS, si no tienes Docker Desktop:

```bash
brew install colima docker docker-compose
colima start --cpu 2 --memory 4 --disk 30
```

Levantar todo (backend + frontend):

```bash
docker-compose up -d --build     # con el plugin: docker compose up -d --build
```

| Servicio | Dirección |
| :--- | :--- |
| Web | http://localhost:3000 |
| API y documentación | http://localhost:8000 · http://localhost:8000/docs |
| Informe semanal | http://localhost:8000/informe-semanal |

Comandos habituales:

```bash
docker-compose ps                          # estado (ambos deben salir "healthy")
docker-compose logs -f backend             # seguir el registro del backend
docker-compose restart backend             # reiniciar un servicio
docker-compose up -d --build               # aplicar cambios de código
docker-compose down                        # parar (los datos se conservan en el volumen)
docker-compose down -v                     # parar y BORRAR la base de datos del volumen
```

Cómo funciona:

- **Primer arranque:** el volumen está vacío, así que el backend **sincroniza todas las fuentes solo** (unos 2 minutos). Hasta que termine, la web muestra solo las 2 convocatorias de ejemplo de `fuentes/`. Se sigue en `GET /api/v1/ingest/runs`.
- **Datos persistentes:** la base de datos SQLite vive en el volumen `reforesta-data` (`/app/data`). Bajar y subir los contenedores no la pierde.
- **Una sola réplica de backend:** SQLite y la sincronización diaria no admiten varias a la vez.
- **Dirección pública del backend:** el navegador llega al backend con `PUBLIC_BACKEND_URL` (por defecto `http://localhost:8000`). En un servidor, ponla antes de construir: `PUBLIC_BACKEND_URL=https://api.tudominio.org docker-compose up -d --build`.
- **Copia de seguridad del volumen:**
  ```bash
  docker run --rm -v 1hack_reforesta_reforesta-data:/data -v "$PWD":/copia alpine tar czf /copia/reforesta-data.tgz -C /data .
  ```

---

## Sincronización diaria

El backend actualiza todas las fuentes **cada día a las 07:00 (Europe/Madrid)**: BDNS, BOE, TED/PLACSP, UE, boletines autonómicos, fundaciones y `fuentes/`. Luego recalcula plazos y estados.

- **Al arrancar** (por ejemplo, tras levantar el contenedor), comprueba si se perdió la última cita de las 07:00 y, si es así, **sincroniza en ese momento**. Si ya se sincronizó después de la última cita, no hace nada.
- **Si falla** una sincronización, reintenta hasta 3 veces con 5 minutos entre intentos.
- **Reloj real:** espera mirando la hora cada minuto, así que una suspensión del equipo no la retrasa.
- **Comprobarlo:** `GET /api/v1/health` muestra la próxima ejecución y `GET /api/v1/ingest/runs` el historial.
- **Manual:** `POST /api/v1/ingest/trigger`.

Una sincronización se da por completada aunque alguna fuente (por ejemplo BDNS) no haya respondido, porque los conectores no propagan sus errores. El resultado de cada fuente está en el detalle de la ejecución.

---

## Informe semanal

Resumen de las convocatorias nuevas de los últimos días, pensado para enviarse por correo en PDF: resumen, las que hay que atender esta semana, las abiertas y las próximas aperturas, cada una con su enlace oficial.

- **Enlace:** `GET /informe-semanal` (HTML, siempre con los datos actuales). Admite `?dias=14` (de 1 a 60; por defecto 7).
- **Archivo:** `python3 scripts/informe_semanal.py` guarda `informes/informe-semanal-AAAA-MM-DD.html` (opciones `--dias`, `--api`, `--salida`). Solo usa la librería estándar.
- **PDF:** abre el HTML e imprime a PDF desde el navegador (A4), o con Chrome:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer \
    --print-to-pdf=informe.pdf file://$PWD/informes/informe-semanal-AAAA-MM-DD.html
  ```
- **Pendiente:** el envío automático por correo (hace falta un canal de envío, como SMTP) y servir el PDF directamente desde el backend.

---

## Desarrollo en local (sin Docker)

Requisitos: **Python 3.11+** y **Node.js 18+**.

```bash
# Backend (:8000)
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # con pruebas; en producción basta requirements.txt
cp .env.example .env                       # opcional: los valores por defecto sirven
.venv/bin/uvicorn app.main:app --port 8000

# Frontend (:3000), en otra terminal
cd frontend
npm install
npm run dev
```

Comprobaciones:

```bash
.venv/bin/pytest -q                        # backend
cd frontend && npx tsc --noEmit && npx eslint src
```

Notas:
- La base SQLite local es `data/reforesta.db` y **no debe estar en una carpeta sincronizada** (OneDrive, Dropbox): el modo WAL falla con un error de E/S.
- El repositorio incluye una base ya sincronizada para que todo el equipo vea los mismos datos. Se modifica cada vez que arranca el backend; **no la incluyas en los commits**.
- En Windows (PowerShell) usa `.\.venv\Scripts\python.exe` y `npm.cmd`.

---

## Configuración

Variables de entorno (`.env`, plantilla en `.env.example`). Las más relevantes:

| Variable | Por defecto | Qué hace |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./data/reforesta.db` | SQLite o PostgreSQL (`postgresql+psycopg://…`). |
| `AUTO_SYNC_ENABLED` | `true` | Activa la sincronización diaria. |
| `DAILY_SYNC_HOUR` / `DAILY_SYNC_MINUTE` / `DAILY_SYNC_TIMEZONE` | `7` / `0` / `Europe/Madrid` | Hora de la sincronización. |
| `SYNC_CATCHUP_ON_STARTUP` | `true` | Al arrancar, recupera la sincronización si se perdió la última cita. |
| `SYNC_RETRY_ATTEMPTS` / `SYNC_RETRY_DELAY_SECONDS` | `3` / `300` | Reintentos si una sincronización falla. |
| `INGEST_START_YEAR` / `INGEST_END_YEAR` | `2016` / `2028` | Horizonte del histórico. |
| `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` | vacías | Clasificación asistida por IA (capa 2). Sin ninguna, se usa el motor determinista local. |
| `PUBLIC_BACKEND_URL` | `http://localhost:8000` | Dirección del backend vista desde el navegador (Docker). |

---

## Cómo está hecho

```text
├── app/                      # Backend FastAPI
│   ├── main.py               # API REST y arranque
│   ├── informe_semanal.py    # Informe semanal en HTML
│   ├── ingestors/            # Conectores (BDNS, BOE, TED/PLACSP, CCAA, SEDIA, fundaciones) y planificador de las 07:00
│   ├── pipeline/             # Filtro en dos capas, PDF/OCR, fechas LPACAP y priorización
│   └── domain/               # Perfil estatutario de Reforesta y motor de elegibilidad
├── frontend/                 # Next.js 16 + React 19 + Tailwind v4 + Leaflet
│   └── src/lib/recurrencia.ts   # Detección de programas que se repiten y medición del acierto
├── scripts/informe_semanal.py   # Informe semanal desde la línea de comandos
├── fuentes/                  # PDF de referencia (MITECO y Comunidad de Madrid)
├── tests/                    # Suite pytest
├── Dockerfile · docker-compose.yml
├── requirements.txt · requirements-dev.txt
├── PLAN_PROYECTO.md          # Diseño técnico del backend
└── REQUERIMIENTOS.md         # Problema, requisitos y estado frente al reto
```

**Filtro de dos capas.** La capa 1 es determinista (patrones, códigos CPV forestales y ambientales, exclusión de ruido). La capa 2 clasifica con IA si hay clave, o con el motor local si no. Después, el motor de elegibilidad aplica los estatutos de Reforesta y expone los requisitos que excluyen cada convocatoria.

**Plazos.** Los días hábiles restantes se calculan según el artículo 30 de la Ley 39/2015, con los calendarios nacional y de las 19 comunidades.

**Previsión.** Agrupa las ediciones de un mismo organismo con títulos parecidos y estima la ventana de apertura (3 meses como máximo). La probabilidad (alta, media o baja) sale de reglas simples sobre cuántos años consecutivos ha salido, y se mide con el propio histórico: cada año se prevé con lo que se sabía a 1 de enero y se compara con lo que ocurrió.

---

## API principal

| Método | Ruta | Uso |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Estado del servicio y próxima sincronización |
| `GET` | `/api/convocatorias` | Convocatorias en el formato de la web (`estado=ABIERTAS\|ACTIVA\|PROXIMA\|CERRADA\|TODAS`) |
| `GET` | `/informe-semanal` | Informe HTML de las convocatorias nuevas (`dias=7`) |
| `GET` | `/api/v1/ingest/runs` | Historial de sincronizaciones |
| `POST` | `/api/v1/ingest/trigger` | Sincronización manual |
| `GET` | `/api/v1/map/summary` | Agregados territoriales |
| `GET` | `/api/v1/stats/historical` | Estadísticas del histórico |
| `GET` | `/api/v1/opportunities/prioritized` | Cola priorizada |
| `GET` | `/api/v1/export/csv` · `/calendar.ics` · `/markdown/{id}` | Exportaciones |
| `POST` | `/api/v1/analyze/text` · `/analyze/pdf` | Análisis puntual de un texto o unas bases en PDF |

Documentación completa en `/docs`.

---

## Antes de abrirlo a internet

El contenedor funciona, pero **no está listo para exponerse**. Falta:

- **Autenticación** en los endpoints de administración (`/api/v1/ingest/trigger` y similares están abiertos) y revisar la CORS, que está abierta.
- **HTTPS y dominio** (un proxy inverso como Caddy o Nginx con certificado).
- **Copias de seguridad** programadas del volumen.
- **Base de datos:** SQLite es válida para una instancia y pocos usuarios; para más, PostgreSQL (el driver ya está incluido).
- **Frontend:** la variable `PUBLIC_BACKEND_URL` se fija al construir la imagen.

---

## Ramas

`main` es la rama de trabajo y despliegue. `back`, `front` y `test` son ramas de desarrollo anteriores; el flujo vigente es trabajar sobre `main`.
