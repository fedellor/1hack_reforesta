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

## Cómo ponerlo en marcha paso a paso (con Docker, la forma más fácil)

Esta aplicación tiene dos partes: el **servidor** (donde están los datos y el buscador automático, llamado *backend*) y la **página web** que ves en pantalla (*frontend*). Con **Docker** no hace falta instalar Python ni Node.js a mano: todo viene empaquetado para que funcione igual en **Windows, macOS y Linux**.

### Paso 1 · Tener Docker instalado y abierto (solo la primera vez)

Elige tu sistema operativo:

- **En Windows:**
  1. Descarga e instala **Docker Desktop para Windows** (durante la instalación deja marcada la opción de WSL 2 si aparece).
  2. **Muy importante:** antes de usar ningún comando, abre la aplicación **Docker Desktop** desde el menú Inicio y espera unos segundos hasta que abajo a la izquierda ponga **Engine running** (con el icono en verde). Si Docker Desktop está cerrado, el servidor no podrá arrancar.
  3. Descarga o guarda este proyecto en una carpeta normal del ordenador (por ejemplo `C:\proyectos\reforesta`). **No lo guardes dentro de OneDrive ni Dropbox**, porque esas carpetas en la nube provocan errores en la base de datos SQLite.

- **En macOS:**
  1. Descarga e instala **Docker Desktop para Mac**, ábrelo y espera a que el icono de la ballena en la barra superior quede quieto.
  2. *Alternativa ligera (si prefieres no usar Docker Desktop en Mac):* abre la aplicación **Terminal** y ejecuta estos dos comandos para preparar Colima:
     ```bash
     brew install colima docker docker-compose
     colima start --cpu 2 --memory 4 --disk 30
     ```

- **En Linux (Ubuntu / Debian):**
  1. Abre la aplicación **Terminal** (atajo `Ctrl + Alt + T`), instala Docker y el plugin de Compose, y activa el servicio:
     ```bash
     sudo apt update && sudo apt install -y docker.io docker-compose-v2
     sudo systemctl enable --now docker
     sudo usermod -aG docker "$USER"
     ```
  2. Cierra tu sesión de usuario y vuelve a entrar (o reinicia) para poder ejecutar Docker sin tener que escribir `sudo` delante cada vez.

---

### Paso 2 · Abrir la ventana de comandos dentro de la carpeta del proyecto

Necesitas una ventana de texto situada dentro de la carpeta donde está este proyecto (`README.md`, `docker-compose.yml`, etc.):

- **En Windows (PowerShell):**
  - *La forma más rápida:* abre la carpeta del proyecto en el **Explorador de archivos**, haz clic derecho en un espacio vacío (sin tocar ningún archivo) y elige **«Abrir en Terminal»**. También puedes hacer clic en la barra de ruta de arriba, escribir `powershell` y pulsar **Enter**.
  - *Otra forma:* abre el menú **Inicio**, busca **Windows PowerShell**, ábrelo, escribe `cd ` seguido de la ruta de tu carpeta (por ejemplo `cd C:\proyectos\reforesta`) y pulsa **Enter**.
- **En macOS (Terminal):**
  - Pulsa `Cmd ⌘ + Espacio`, escribe **`Terminal`** y pulsa **Enter**. Escribe `cd ` (con un espacio al final), arrastra la carpeta del proyecto dentro de esa ventana y pulsa **Enter**.
- **En Linux (Terminal):**
  - Haz clic derecho dentro de la carpeta del proyecto y pulsa **«Abrir en terminal»**, o abre **Terminal** (`Ctrl + Alt + T`) y muévete a la carpeta con `cd /ruta/hasta/la/carpeta`.

---

### Paso 3 · Pegar el comando que enciende la aplicación

Dentro de esa ventana de PowerShell o Terminal, copia y pega esta línea exacta y pulsa **Enter** (es la misma en Windows, macOS y Linux):

```bash
docker compose up -d --build
```

*(Si tienes un Docker antiguo que te da error con `compose`, escríbelo con guion: `docker-compose up -d --build`.)*

**Qué va a pasar ahora:**
- **La primera vez** tardará entre **3 y 5 minutos** mientras descarga los componentes y monta el servidor y la web. Cuando termine y puedas volver a escribir en la ventana, ya estará encendido funcionando en segundo plano (puedes incluso cerrar PowerShell o Terminal sin apagarlo).
- Al encenderse con una base de datos vacía, el servidor empieza a **descargar y analizar por su cuenta todas las ayudas oficiales** (tarda **unos 2 minutos**). Si abres la web enseguida y solo ves 2 ayudas de ejemplo (`fuentes/`), es completamente normal: espera un par de minutos y recarga la página en el navegador (`F5`).

---

### Paso 4 · Abrir la web en tu navegador

Abre Chrome, Edge, Safari o Firefox y entra en estas direcciones:

| Qué quieres abrir | Dirección para pegar en el navegador |
| :--- | :--- |
| **Aplicación web (Radar Reforesta)** | http://localhost:3000 |
| **Panel técnico / documentación de la API** | http://localhost:8000/docs |
| **Estado del servidor y base de datos** | http://localhost:8000/api/v1/health |
| **Informe semanal listo para imprimir en PDF** | http://localhost:8000/informe-semanal |

---

### Comandos del día a día (copiar y pegar cuando los necesites)

Abre PowerShell (Windows) o Terminal (macOS/Linux) en la carpeta del proyecto y usa el que necesites:

| Qué quieres hacer | Comando |
| :--- | :--- |
| **Comprobar si ya está todo sano** (ambos servicios deben poner `(healthy)`) | `docker compose ps` |
| **Ver en directo qué está haciendo el servidor** (útil para ver cómo avanza la descarga inicial; pulsa **`Ctrl + C`** cuando quieras salir sin apagar nada) | `docker compose logs -f backend` |
| **Apagar la aplicación** (tus datos guardados **no se borran**; la próxima vez arranca rápido con todo intacto) | `docker compose down` |
| **Volver a encenderla sin reconstruir nada** (tras haberla apagado) | `docker compose up -d` |
| **Reiniciar el servidor** si se queda atascado | `docker compose restart backend` |
| **Aplicar cambios nuevos** después de actualizar el proyecto (`git pull`) | `docker compose up -d --build` |
| **Apagar y BORRAR toda la base de datos** para empezar de cero | `docker compose down -v` |

Notas importantes de funcionamiento con Docker:
- **Dónde se guardan los datos:** la base de datos SQLite vive dentro de un almacén persistente de Docker llamado `reforesta-data` (`/app/data`). Apagar y encender con `docker compose down` y `docker compose up -d` conserva todos tus datos.
- **Un único servidor a la vez:** SQLite y la sincronización diaria de las 07:00 no admiten varias copias del backend funcionando a la vez.
- **Si algún día lo subes a un servidor con dominio propio:** la web necesita saber la dirección pública del backend en el momento de construir la imagen.
  - En **Windows (PowerShell)**:
    ```powershell
    $env:PUBLIC_BACKEND_URL="https://api.tudominio.org"
    docker compose up -d --build
    ```
  - En **macOS y Linux (Terminal)**:
    ```bash
    PUBLIC_BACKEND_URL=https://api.tudominio.org docker compose up -d --build
    ```
- **Hacer una copia de seguridad de los datos:** primero mira el nombre exacto de tu volumen ejecutando `docker volume ls` (suele llamarse `reforesta_reforesta-data` o `1hack_reforesta_reforesta-data`) y luego guarda la copia `reforesta-data.tgz` en tu carpeta actual:
  - En **Windows (PowerShell):**
    ```powershell
    docker run --rm -v reforesta_reforesta-data:/data -v "${PWD}:/copia" alpine tar czf /copia/reforesta-data.tgz -C /data .
    ```
  - En **macOS y Linux (Terminal):**
    ```bash
    docker run --rm -v 1hack_reforesta_reforesta-data:/data -v "$PWD":/copia alpine tar czf /copia/reforesta-data.tgz -C /data .
    ```
    *(Sustituye el nombre del volumen antes de `:/data` si `docker volume ls` te muestra otro distinto.)*

---

## Sincronización diaria

El servidor busca y actualiza todas las fuentes automáticamente **todos los días a las 07:00 (hora peninsular, `Europe/Madrid`)**: BDNS, BOE, TED/PLACSP, UE, boletines autonómicos, fundaciones y los PDF locales de `fuentes/`. Después recalcula automáticamente los días hábiles restantes y el estado de cada convocatoria.

- **Si el ordenador o contenedor estuvo apagado a las 07:00:** nada más encenderlo comprueba si se perdió la última sincronización diaria y, si falta, la ejecuta en ese momento. Si ya se actualizó hoy después de las 07:00, no repite trabajo innecesario.
- **Si falla por un corte puntual:** reintenta hasta 3 veces esperando 5 minutos entre intentos.
- **Reloj real:** revisa la hora del sistema cada minuto, así que si el ordenador entra en suspensión no pierde la hora prevista.
- **Para comprobar cuándo fue la última o forzar una ahora mismo:**
  - Ver última ejecución e historial: abre http://localhost:8000/api/v1/ingest/runs en el navegador.
  - Lanzar una sincronización manual ahora mismo: desde http://localhost:8000/docs (endpoint `POST /api/v1/ingest/trigger`) o por consola.

Una sincronización se da por completada aunque alguna fuente concreta (por ejemplo BDNS) haya fallado puntualmente, porque cada conector está aislado para no tumbar el resto. En `/api/v1/ingest/runs` puedes ver cuántas convocatorias trajo cada fuente.

---

## Informe semanal (listo para enviar por correo en PDF)

Es un resumen visual con las convocatorias nuevas de los últimos días, las que conviene revisar esta semana, las abiertas y las próximas aperturas, cada una con su enlace oficial.

- **Forma más fácil (sin comandos):** con la aplicación encendida, abre **http://localhost:8000/informe-semanal** en tu navegador habitual (puedes añadir `?dias=14` al final para ver 14 días, admite entre 1 y 60). Después pulsa **`Ctrl + P`** (Windows/Linux) o **`Cmd ⌘ + P`** (macOS) y elige **«Guardar como PDF»** en formato A4.
- **Guardar el informe como archivo HTML desde consola:**
  - En **Windows (PowerShell):** `python scripts\informe_semanal.py`
  - En **macOS y Linux (Terminal):** `python3 scripts/informe_semanal.py`
  Esto crea el archivo `informes/informe-semanal-AAAA-MM-DD.html` (acepta `--dias 14`, `--api http://localhost:8000`, `--salida ruta.html`). Solo usa librerías estándar de Python.
- **Pasar ese HTML a PDF desde consola (opcional):**
  - En **Windows (PowerShell):**
    ```powershell
    & "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --no-pdf-header-footer --print-to-pdf=informe.pdf "$PWD\informes\informe-semanal-AAAA-MM-DD.html"
    ```
  - En **macOS (Terminal):**
    ```bash
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=informe.pdf "file://$PWD/informes/informe-semanal-AAAA-MM-DD.html"
    ```
  - En **Linux (Terminal):**
    ```bash
    google-chrome --headless=new --no-pdf-header-footer --print-to-pdf=informe.pdf "file://$PWD/informes/informe-semanal-AAAA-MM-DD.html"
    ```
- **Pendiente de implementar:** el envío automático por correo (requiere configurar un servidor de envío SMTP) y descargar el PDF directamente desde un botón del servidor.

---

## Arrancar sin Docker (en local, para desarrollar o hacer pruebas)

Si prefieres encenderlo directamente en tu ordenador sin usar Docker, necesitas tener instalados **Python 3.11 o superior** y **Node.js 18 o superior**. Tendrás que abrir **dos ventanas** a la vez: una mantiene encendido el servidor y la otra mantiene encendida la página web.

### En Windows (usando PowerShell)

1. **Primera ventana de PowerShell (para el servidor en `http://localhost:8000`):**
   Entra en la carpeta del proyecto (recuerda: **fuera de OneDrive**) y pega estos comandos uno tras otro:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   copy .env.example .env
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
   ```
   *(Usamos directamente `.\.venv\Scripts\python.exe` para que no necesites activar el entorno y no te bloquee PowerShell por políticas de empresa. Si solo quieres ejecutarlo sin herramientas de pruebas, puedes instalar `requirements.txt` en lugar de `requirements-dev.txt`.)*

2. **Segunda ventana de PowerShell (para la web en `http://localhost:3000`):**
   Abre otra ventana de PowerShell en la carpeta del proyecto y pega:
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```

3. **Cuando quieras pasar los tests automáticos (opcional):**
   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   cd frontend; npx.cmd tsc --noEmit; npx.cmd eslint src
   ```

### En macOS y Linux (usando Terminal)

1. **Primera ventana de Terminal (para el servidor en `http://localhost:8000`):**
   Dentro de la carpeta del proyecto, pega:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements-dev.txt   # con pruebas; en producción basta requirements.txt
   cp .env.example .env                           # opcional: los valores por defecto sirven
   .venv/bin/uvicorn app.main:app --port 8000
   ```

2. **Segunda ventana de Terminal (para la web en `http://localhost:3000`):**
   Abre otra ventana de Terminal en la carpeta del proyecto y pega:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Comprobaciones automáticas (opcional):**
   ```bash
   .venv/bin/pytest -q                        # pruebas del servidor
   cd frontend && npx tsc --noEmit && npx eslint src
   ```

Notas importantes para el arranque en local:
- La base SQLite local es `data/reforesta.db` y **no debe estar en una carpeta sincronizada** (OneDrive, Dropbox): el modo WAL falla con un error de lectura/escritura.
- El repositorio incluye una base `data/reforesta.db` ya sincronizada para que todo el equipo parta de los mismos datos. Ese archivo cambia cada vez que arranca el servidor; **no lo incluyas en tus commits** de Git.

---

## Configuración

Si quieres ajustar algún comportamiento (por ejemplo, añadir claves de IA o cambiar la hora diaria de búsqueda), copia `.env.example` a un archivo llamado `.env` en la raíz y modifica lo que necesites:

| Variable | Por defecto | Qué hace |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./data/reforesta.db` | Base de datos SQLite local o PostgreSQL (`postgresql+psycopg://…`). |
| `AUTO_SYNC_ENABLED` | `true` | Activa o desactiva la sincronización diaria automática. |
| `DAILY_SYNC_HOUR` / `DAILY_SYNC_MINUTE` / `DAILY_SYNC_TIMEZONE` | `7` / `0` / `Europe/Madrid` | Hora a la que rastrea las fuentes cada día. |
| `SYNC_CATCHUP_ON_STARTUP` | `true` | Al arrancar, recupera la sincronización si el equipo estuvo apagado a la hora prevista. |
| `SYNC_RETRY_ATTEMPTS` / `SYNC_RETRY_DELAY_SECONDS` | `3` / `300` | Cuántas veces reintenta si falla y cuántos segundos espera entre reintentos. |
| `INGEST_START_YEAR` / `INGEST_END_YEAR` | `2016` / `2028` | Rango de años del histórico. |
| `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` | vacías | Claves opcionales de IA para la capa 2. Si están vacías (o sin cuota), el motor determinista local clasifica sin depender de internet. |
| `PUBLIC_BACKEND_URL` | `http://localhost:8000` | Dirección del backend vista desde el navegador (al construir Docker). |

---

## Cómo está hecho

```text
├── app/                         # Servidor FastAPI (backend)
│   ├── main.py                  # API REST y arranque
│   ├── informe_semanal.py       # Informe semanal en HTML
│   ├── ingestors/               # Conectores (BDNS, BOE, TED/PLACSP, CCAA, SEDIA, fundaciones) y planificador de las 07:00
│   ├── pipeline/                # Filtro en dos capas, lectura de PDF/OCR, cálculo de plazos LPACAP y priorización
│   └── domain/                  # Perfil estatutario de Reforesta y motor de elegibilidad
├── frontend/                    # Web en Next.js 16 + React 19 + Tailwind v4 + Leaflet
│   └── src/lib/recurrencia.ts   # Detección de programas que se repiten y medición del acierto
├── scripts/informe_semanal.py   # Generador del informe semanal desde consola
├── fuentes/                     # PDF de referencia (MITECO y Comunidad de Madrid)
├── tests/                       # Suite de pruebas pytest
├── Dockerfile · docker-compose.yml
├── requirements.txt · requirements-dev.txt
├── PLAN_PROYECTO.md             # Diseño técnico detallado del backend
└── REQUERIMIENTOS.md            # Problema, requisitos y estado frente al reto
```

- **Filtro en dos capas:** la capa 1 filtra de forma determinista (palabras clave, códigos CPV forestales y ambientales y exclusiones de ruido). La capa 2 evalúa con IA si hay una clave configurada con saldo, o con el motor local experto si no. Después, el motor de elegibilidad aplica los estatutos de Reforesta y señala los requisitos que excluyen cada convocatoria.
- **Plazos:** los días hábiles restantes se calculan según el artículo 30 de la Ley 39/2015, teniendo en cuenta el calendario nacional y el de las 19 comunidades autónomas.
- **Previsión:** agrupa las ediciones históricas de un mismo organismo con títulos parecidos y estima la ventana de apertura (3 meses como máximo). La probabilidad (alta, media o baja) sale de cuántos años seguidos ha salido, y se contrasta contra el propio histórico año a año.

---

## API principal

| Método | Ruta | Uso |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Estado del servicio, conteo de ayudas y próxima sincronización |
| `GET` | `/api/convocatorias` | Convocatorias en el formato de la web (`estado=ABIERTAS\|ACTIVA\|PROXIMA\|CERRADA\|TODAS`) |
| `GET` | `/informe-semanal` | Informe HTML de las convocatorias nuevas (`dias=7`) |
| `GET` | `/api/v1/ingest/runs` | Historial de sincronizaciones |
| `POST` | `/api/v1/ingest/trigger` | Lanzar una sincronización manual |
| `GET` | `/api/v1/map/summary` | Totales agrupados por comunidad autónoma |
| `GET` | `/api/v1/stats/historical` | Estadísticas del histórico |
| `GET` | `/api/v1/opportunities/prioritized` | Cola priorizada de oportunidades |
| `GET` | `/api/v1/export/csv` · `/calendar.ics` · `/markdown/{id}` | Descarga en CSV, calendario ICS o ficha Markdown |
| `POST` | `/api/v1/analyze/text` · `/analyze/pdf` | Análisis puntual de un texto o unas bases en PDF |

Documentación interactiva completa en `/docs`.

---

## Antes de abrirlo a internet

La aplicación en Docker funciona lista para usar en red local o en demostraciones, pero **no está preparada para exponerse abierta en internet** sin añadir antes:

- **Autenticación** en las rutas de administración (ahora `/api/v1/ingest/trigger` y similares están abiertos) y restricción de CORS.
- **HTTPS y dominio propio** delante (por ejemplo con Caddy o Nginx con certificado SSL).
- **Copias de seguridad** programadas del volumen de datos.
- **Base de datos:** SQLite funciona bien para una instancia y pocos usuarios; si van a entrar muchas personas a la vez, conviene cambiar `DATABASE_URL` a PostgreSQL (el conector ya viene incluido).
- **Frontend:** configurar `PUBLIC_BACKEND_URL` con la dirección pública antes de construir la imagen.

---

## Ramas

`main` es la rama de trabajo y despliegue. `back`, `front` y `test` son ramas de desarrollo anteriores; el flujo actual trabaja directamente sobre `main`.
