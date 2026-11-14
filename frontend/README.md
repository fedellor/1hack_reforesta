# Frontend · Radar Reforesta

Interfaz web interna del equipo de Asociación Reforesta. Next.js 16 (App Router), React 19, Tailwind CSS v4 y Leaflet (mapa sin teselas externas).

> Esta versión de Next.js tiene cambios respecto a lo habitual. Antes de usar una API de Next, consulta la guía correspondiente en `node_modules/next/dist/docs/` (ver `AGENTS.md`).

## Qué hay en `src/`

| Archivo | Responsabilidad |
| :--- | :--- |
| `app/page.tsx` | Contenedor: carga de datos, filtros y cambio de sección |
| `app/api/convocatorias/route.ts` | Proxy hacia el backend; devuelve 502 si no responde |
| `services/api.ts` | Llamadas al backend y adaptación de su formato al contrato de la web |
| `components/Header.tsx` · `Hero.tsx` · `FilterBar.tsx` | Menú, banner con las cifras del embudo y barra de filtros |
| `components/MapView.tsx` · `LeafletMap.tsx` | **Mapa**: reparto territorial, buscador y panel por comunidad |
| `components/PlanView.tsx` | **Plan de ataque**: cierres por mes con selector de mes y año |
| `components/EmpresasView.tsx` | **Empresas**: fundaciones y mecenazgo |
| `components/PrevisionView.tsx` · `ProgramaDrawer.tsx` | **Previsión**: lo que suele salir cada mes y la medición de acierto |
| `components/HistoricoView.tsx` | **Histórico**: archivo de convocatorias cerradas con filtros |
| `components/ConvocatoriaDrawer.tsx` | Ficha de una convocatoria |
| `lib/recurrencia.ts` | Detección de programas que se repiten y medición del acierto de la previsión |
| `lib/search.ts` | Buscador sin tildes, con siglas (`MITECO`, `BDNS`, `PEPAC`…) |
| `lib/territorio.ts` · `plazo.ts` · `texto.ts` | Territorio y licitaciones, plazos y limpieza de textos del backend |
| `types/convocatoria.ts` | Contrato de datos con el backend |
| `public/data/*.geojson` | Geometrías del mapa, sin dependencias externas |

## Arranque

```bash
npm install
npm run dev          # desarrollo, http://localhost:3000
npm run build && npm run start   # producción
npx tsc --noEmit && npx eslint src   # comprobaciones
```

Necesita el backend en marcha (por defecto `http://localhost:8000`). Para el conjunto con Docker, ver el README de la raíz.

## Variables de entorno

| Variable | Qué hace |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Dirección del backend **desde el navegador**. Se fija al construir. Si falta, usa el mismo servidor en el puerto 8000. |
| `BACKEND_INTERNAL_URL` | Dirección del backend **desde el servidor de Next** (en Docker, `http://backend:8000`). Tiene prioridad sobre la anterior en el proxy. |
