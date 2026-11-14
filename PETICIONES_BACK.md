# Peticiones del front al backend

Cosas que el front ya consume o necesita y que dependen de la rama `back`. Ordenadas por impacto.

## 1. Fechas reales en el histórico (afecta a la previsión)
La previsión de recurrencia (`frontend/src/lib/recurrencia.ts`) deduce el mes habitual de cada programa a partir de `fechaPublicacion`.
En `to_frontend_convocatoria`, cuando falta la fecha se rellena con valores inventados:

- `fechaPublicacion` → `{anio}-01-15`
- `fechaCierre` → `{anio}-12-31`

Con esos valores todos los programas «se publican en enero» y la previsión sale falsa. **Pedimos** enviar `null` (o un campo `fechaPublicacionEstimada: true`) cuando la fecha no sea real, y que el front las ignore. El front ya trata `fecha_fin_solicitud = null` como «abierta sin plazo» solo para convocatorias vigentes.

## 2. Elegibilidad con el perfil real de Reforesta
Hoy: `elegible = "ONG_FUNDACIONES" in beneficiarios_tipos or tipo_oportunidad != "LICITACION"`. Casi todo sale apto (en los datos de ejemplo, 44 de 48 no tienen ningún dealbreaker), así que el filtro que más tiempo ahorra no se está ejerciendo.

Datos de los estatutos (2026) que deberían alimentar la regla:

| Dato | Valor | Dealbreaker que permite detectar |
|---|---|---|
| Forma jurídica | Asociación sin ánimo de lucro (no fundación) | «solo fundaciones», «solo PYMES», «solo entidades locales» |
| Declaración | Utilidad Pública | «exige declaración de utilidad pública» → apta; «exige otra figura» → no |
| Constitución | 1991 (35 años) | «antigüedad mínima» |
| Ámbito | Estatal | convocatorias de cualquier CCAA son elegibles |
| Actividad fuera de España | Permitida, con atención a países en desarrollo (art. 4) | no descartar cooperación internacional por ser extranjera |
| Patrimonio fundacional | 50.000 pts (≈ 300 €) | requisitos de solvencia / patrimonio mínimo |

Cada exclusión debe devolver la **cláusula literal** y el artículo (ya soportado: `dealbreakers`, `motivoElegibilidad`).

## 3. Fines estatutarios más allá de las 3 líneas actuales
Art. 3 de los estatutos incluye, además de restauración, hábitats y educación: inclusión social y discapacidad (7-9), igualdad de género (6), cooperación internacional (5), agroecología (13), custodia del territorio (14), I+D (15), ciencia ciudadana (16), economía sostenible (17) y responsabilidad social corporativa (10).
Hoy `matchingLineas` solo puntúa 3 y puede estar infravalorando convocatorias legítimas. **Pedimos**: ampliar la clasificación y exponer `categorias` en el contrato del front (hoy solo está en `/api/v1/opportunities`, no en `/api/convocatorias`), para poder filtrar por línea.

## 4. Histórico: volumen y forma
El front pide `GET /api/convocatorias?estado=TODAS` y filtra en el navegador. Funciona bien con cientos o pocos miles de filas. Si el histórico crece mucho, conviene paginar o exponer los filtros que ya existen en `/api/v1/opportunities` (`q`, `anio_desde`, `anio_hasta`, `ccaa`…) en el endpoint del puente.
Para que la recurrencia agrupe bien, el título debe ser estable entre años (sin que cambie el órgano o la redacción de la convocatoria).

## 5. Calendario predictivo del backend
`/api/v1/opportunities/predictive-calendar` usa una lista fija de programas escrita a mano. El front calcula la previsión desde el histórico, así que la lista del backend queda como apoyo (checklists de preparación por programa). Si se prefiere un único origen, el algoritmo de `recurrencia.ts` es portable a Python.
