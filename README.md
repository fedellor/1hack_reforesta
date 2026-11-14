# 🌲 Radar Reforesta · Consola de Financiación y Decisión Territorial
> Proyecto desarrollado para el reto **1hack A Coruña — El reto de Reforesta**, impulsado por **Common Seeds (The Agile Monkeys)**.

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-06B6D4?logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)

---

## 1. El Problema Real que Resolvemos

> *"Cada convocatoria que se le escapa a Reforesta es monte que no se planta."*

**Reforesta** es una ONG ambiental con más de 30 años de historia, declarada de Utilidad Pública, con un equipo de 6-7 personas. Financia cada hectárea que restaura mediante subvenciones públicas o mecenazgo corporativo.

Pese a que en España arden más de 300.000 hectáreas al año y existe abundante financiación disponible:
1. **Cuello de botella de búsqueda:** Reforesta solo presenta **4 o 5 solicitudes al año**, encontradas manualmente en Google o revisando siempre las mismas 4 fuentes (MITECO, Fundación Biodiversidad, CAM ambiental y Agenda 2030). Cientos de ayudas de CCAA, diputaciones y programas europeos se les escapan.
2. **El "peaje de lectura" administrativo:** Analizar si una convocatoria encaja exige leer entre 30 y 80 páginas de bases legales en boletines oficiales (BOE, BOCM, DOG...). Con frecuencia, tras horas de lectura, descubren en la página 35 un requisito formal excluyente (*dealbreaker*) que invalida su candidatura.
3. **El canal de empresas (RSC / ESG) está a cero:** Solo atienden a las empresas que acuden a ellos por iniciativa propia.

---

## 2. Nuestra Solución: *Zero-Search Observability*

### ❌ Por qué NO hicimos un chatbot conversacional
Un chatbot tradicional obliga al usuario a pensar qué preguntas hacer a ciegas (*"¿Hay subvenciones en Madrid?"*), genera respuestas lentas, sufre de alucinaciones y no ofrece una panorámica estratégica de los fondos disponibles.

### ✅ Qué es "Radar Reforesta"
Una **Consola Ejecutiva de Decisión**:
* **La búsqueda no ocurre en el frontend:** El backend rastrea periódicamente fuentes oficiales, pre-procesa las bases legales con un embudo LLM en 2 fases y clasifica cada oportunidad según los estatutos de Reforesta.
* **El frontend expone la máxima densidad informativa útil:** El equipo entra y en menos de 30 segundos sabe si una convocatoria encaja, cuánto dinero ofrece, qué porcentaje de cofinanciación exige, cuándo vence y qué gastos directos cubre.

---

## 3. Los 6 Datos Críticos para la Decisión en < 30 Segundos

| Dato Crítico | Resolución del Dolor de Reforesta |
| :--- | :--- |
| **1. Semáforo de Elegibilidad (Dealbreakers)** | Descarte inmediato: detecta si la convocatoria admite ONGs de Utilidad Pública o si está reservada a PYMES mercantiles, citando el artículo excluyente. |
| **2. Finanzas & Cofinanciación** | Cuantía máxima por proyecto y porcentaje de cofinanciación requerida (ej. *100% subvencionable* vs *requiere 20% fondos propios*). |
| **3. Urgencia y Ventana de Plazo** | Contador visual de días restantes con código cromático (🔴 &lt;7d, 🟡 &lt;20d, 🟢 &gt;20d). |
| **4. Matching Semántico Multidimensional (0–100%)** | Puntuación ponderada en las 3 líneas de Reforesta: **Restauración vegetal**, **Hábitats/biodiversidad** y **Educación ambiental**, con citas textuales literales de las bases oficiales. |
| **5. Acciones Financiables Directas** | Lista de conceptos cubiertos: compra de planta autóctona, desbroces, charcas para anfibios, jornadas escolares, nóminas de personal técnico. |
| **6. Trazabilidad Oficial (Cero Alucinaciones)** | Enlace inmutable al PDF original publicado en el boletín oficial y acceso directo a la sede electrónica de tramitación. |

---

## 4. Estructura del Frontend

Interfaz corporativa con la identidad de reforesta.es (verde `#6aa43a`, crema `#f6f4ee`, carbón `#333`, negro `#141414`; Open Sans y Merriweather; barra de utilidad, menú de 70 px y pie institucional). Plataforma **de uso interno** (sin secciones públicas, `noindex`). Cinco secciones en el menú (Calendario es una vista dentro de Convocatorias), **cada una responde a una pregunta distinta** para no repetir la misma información con otro formato:

| Sección | Pregunta | Qué muestra |
| :--- | :--- | :--- |
| **Mapa** (inicio) | ¿Dónde? | Coropleta por comunidad autónoma (Leaflet + GeoJSON propio, sin teselas externas). Al pulsar una comunidad el mapa hace zoom animado y la divide en **provincias**, coloreadas por sus convocatorias *propias* (diputaciones, ayuntamientos). El panel lateral separa «En toda la comunidad» (aplica a todas las provincias) de «Por provincia». Va precedido del embudo *detectadas → aptas → cierran en 30 días → encaje ≥ 80%*, con la cifra de detectadas real de la última ingesta. |
| **Convocatorias** | ¿Cuáles? | El único listado detallado. Orden de lectura de cada fila: plazo (días en grande, con color de urgencia) → qué es y por qué encaja (cita literal de las bases, o la justificación del radar si no hay cita) → dinero y coste real (cofinanciación y modalidad de pago) → veredicto, encaje y afinidad en las 3 líneas. Filtros: territorio, solo aptas, cierre ≤ 30 días, encaje ≥ 80%, cuantía y orden. |
| **Convocatorias › Calendario** | ¿Cuándo? | **Plan de ataque**: línea de tiempo (30/60/90 días) con una fila por convocatoria, tramo de margen para decidir, tramo de preparación estimada (14 días, constante `PREPARACION_DIAS`), rombo de cierre, aviso «Empezar ya» y carga de cierres por semana. La vista **Mes** es un calendario clásico con panel de próximos cierres. |
| **Histórico** | ¿Qué hubo y qué volverá? | **Buscar:** búsqueda dinámica en las convocatorias desde 2020 (texto, territorio, años, abiertas/cerradas, solo aptas), con distribución por año clicable. **Previsión:** detecta programas que se repiten (órgano + título sin años, con ediciones en ≥ 2 años), estima el mes habitual, el plazo típico y cuándo empezar a preparar (45 días antes), con horizonte de 3/6/12/24 meses y fiabilidad. Avisa de los que «debían haber salido y no constan». |
| **Empresas** | ¿Quién financia? | Tarjetas por entidad para el canal de mecenazgo RSC (hoy a cero): por qué encaja, qué cubre, cuánto aporta, plazo, si el programa se repite cada año (a partir del histórico) y enlaces directos a bases y sede. |
| **Pipeline** | ¿En qué estado? | Seguimiento del equipo: *Nueva*, *Priorizada*, *En preparación*, *Presentada*, *Descartada*. Cada columna ordenada por urgencia y con tope de 5 tarjetas. El cambio de estado se guarda en el backend. |

* **Ficha ejecutiva (panel lateral):** detalle completo con elegibilidad, citas, gastos subvencionables, solvencia, orografía y exportación a Markdown.
* La plataforma trabaja por defecto con una ventana de **30 días**.

* **Plazos:** las convocatorias abiertas sin fecha fin (`plazos.urgencia = abierta_pendiente_plazo`) se muestran como «Abierta · sin plazo fijado», no como «0 días»; no cuentan como cierre en 30 días y no aparecen en el calendario. Con datos de ejemplo los días se recalculan desde la fecha de cierre (`src/lib/plazo.ts`).
* **Cabecera:** franja fina de título con la imagen de reforesta.es, para que el contenido quede en primer plano.

* **Novedades:** el menú muestra cuántas convocatorias son nuevas desde tu última visita (se guarda en el navegador, sin correo ni servidor). Funciona igual con cualquier frecuencia de publicación.
* **Histórico:** se pide a `GET /api/convocatorias?estado=TODAS` solo al entrar en Histórico o Empresas. Sin backend no hay datos de ejemplo del histórico y la sección lo indica. Lo que necesita el front del backend está en [`PETICIONES_BACK.md`](PETICIONES_BACK.md).

### Datos en vivo
* La web lee del backend (`GET /api/convocatorias` y `GET /api/v1/ingest/runs`) y se **refresca sola cada minuto** y al volver a la pestaña. Un indicador arriba a la derecha muestra el estado: *En vivo · actualizado hace N min*, *Datos de ejemplo · radar sin conexión* (ámbar) o *Cargando…*.
* `src/services/api.ts` adapta el contrato del backend al del front: códigos `ES-XX` → nombre de comunidad, `ES`/`EU`/privadas → *Estatal*, y `ubicacion.provincia_nombre` → provincia.
* `src/lib/texto.ts` limpia los textos del backend: separa las citas literales de la justificación generada por el radar, y convierte códigos internos (`ONG_FUNDACIONES`, `prevencion_incendios`…) en texto legible.
* **Si el backend no responde**, la web usa datos de ejemplo (`src/data/mockConvocatorias.ts` y `src/data/mockMapaCompleto.ts`, desactivables con `USAR_DATOS_MAPA_COMPLETO`) y lo indica con claridad.

### Limitaciones conocidas
* **Pipeline:** el backend marca como *priorizada* toda convocatoria con puntuación ≥ 85, de modo que con datos reales casi todo cae en esa columna y se mezcla recomendación del radar con decisión del equipo. Propuesta (rama `back`): dejar todo en *nueva* y enviar la prioridad como campo aparte para mostrarla como etiqueta.
* **Mapa:** las convocatorias estatales (más europeas y privadas) dominan el ranking de dinero y las comunidades quedan con barras pequeñas.
* Pendiente de decidir: capas acumuladas en el mapa (estatal + autonómica + diputación = total disponible para un proyecto en una provincia).

---

## 5. Validación con Convocatorias Reales del Reto

El sistema incluye y valida casos reales facilitados por la organización y entidades oficiales:

1. **MITECO · BDNS 923290:**
   * *Título:* Ayudas para actividades de interés general en investigación y protección del medio ambiente.
   * *Diagnóstico:* 🟢 96% Match · 150.000 € · 100% subvencionado · 8 días restantes · Cita directa a restauración vegetal y charcas de anfibios.
2. **Comunidad de Madrid · Orden 1689/2026:**
   * *Título:* Subvenciones a entidades sin ánimo de lucro para actividades ambientales en la CAM.
   * *Diagnóstico:* 🟢 91% Match · 45.000 € · Requiere 10% cofinanciación · 17 días restantes · Cita a control de ailanto y conservación del tritón ibérico en Guadarrama.
3. **Xunta de Galicia · DOG Reforestación Montes Veciñais:**
   * *Diagnóstico:* 🟢 88% Match · 60.000 € · Reforestación con frondosas autóctonas tras incendios.
4. **Fundación Banco Santander · Bosques de Impacto (RSC):**
   * *Diagnóstico:* 🟢 86% Match · 35.000 € · Mecenazgo privado con voluntariado corporativo.
5. **Ejemplo Negativo de Exclusión (Dealbreaker Detectado):**
   * *Diagnóstico:* 🔴 15% Match · **EXCLUIDA:** Artículo 3.1 reserva las ayudas exclusivamente a PYMES mercantiles (SL/SA). Ahorro directo de lectura de 68 páginas de bases.

---

## 6. Arquitectura y Reparto de Ramas en Git

```
                             ARQUITECTURA DEL PROYECTO
                             
   [ Fuentes Públicas: BDNS API / BOE / CCAA ]       [ Fondos Privados: RSC / Fundaciones ]
                         │                                            │
                         └──────────────────────┬─────────────────────┘
                                                ▼
                                    RAMA 'back' (Backend / IA)
                                 Pipeline en 2 fases con LLM
                              (Heurística + Extracción Quirúrgica)
                                                │
                                                ▼
                                       CONTRATO DE DATOS
                                    (TypeScript / JSON Schema)
                                                │
                                                ▼
                                    RAMA 'front' (Frontend)
                                   Next.js + Tailwind CSS v4
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
                  [ Mapa + Convocatorias    [ Empresas RSC ]        [ Pipeline +
    + Calendario ]                                     Ficha Ejecutiva ]
```

* **Rama `front` (Frontend):** Aplicación Next.js (React 19, Tailwind v4, Leaflet, lucide-react) ubicada en `/frontend` con tipado estricto, mock dinámico en `/api/convocatorias` y cliente de fallback automático a la API de backend.
* **Rama `back` (Backend):** Conectores a la API pública de la BDNS (`infosubvenciones.es`), boletines oficiales y extractor estructurado con LLM.

---

## 7. Instrucciones para Ejecutar el Proyecto en Local

### Requisitos previos
* Node.js v18+ (probado en v26)
* npm v9+
* Para datos reales: Python 3.10+ (el Python 3.9 del sistema en macOS no sirve para el backend)

### Puesta en marcha rápida
```bash
# 1. Clonar el repositorio y situarse en la rama front
git clone https://github.com/fedellor/1hack_reforesta.git
cd 1hack_reforesta
git checkout front

# 2. Entrar en la carpeta del frontend e instalar dependencias
cd frontend
npm install

# 3. Iniciar el servidor de desarrollo
npm run dev
```

Abre en tu navegador: **`http://localhost:3000`**

### Conectar con el backend (datos reales)
```bash
# En otra terminal, desde la rama back (requiere Python 3.10 o superior)
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
La web busca el backend en `http://localhost:8000`. Para otra dirección, define `NEXT_PUBLIC_API_URL` (por ejemplo en `frontend/.env.local`). Sin backend funciona con datos de ejemplo.

> El mapa funciona sin conexión: los límites están en `frontend/public/data/ccaa.geojson` (comunidades) y `frontend/public/data/provincias.geojson` (provincias).

### Compilar para producción
```bash
npm run build
npm run start
```

---

## 8. Impacto Cuantificable para Reforesta

* 📈 **x2 en Solicitudes:** Capacidad para pasar de 4-5 a más de 10 solicitudes al año con el mismo equipo de 6-7 personas.
* 🏢 **2–4 Empresas Captadas:** Activación del canal de mecenazgo privado RSC que anteriormente estaba a cero.
* 🌲 **Más Horas en el Monte:** Eliminación del 85% de las horas dedicadas a leer bases administrativas estériles, traduciendo ese tiempo en más hectáreas restauradas.
