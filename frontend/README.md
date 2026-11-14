# Frontend · Radar Reforesta (`Next.js 16 + React 19`)

Interfaz web de uso interno para el equipo de **Asociación Reforesta**, construida con **Next.js 16 (App Router + Turbopack)**, **React 19**, **Tailwind CSS v4** y **Leaflet** (coropleta sin teselas externas).

---

## Vistas y Módulos (`src/`)

| Ruta / Archivo | Responsabilidad |
| :--- | :--- |
| `src/app/page.tsx` | Contenedor principal, estado global de filtros, carga contra API y enrutado entre secciones |
| `src/app/api/convocatorias/route.ts` | Proxy interno Next.js hacia el backend FastAPI (`NEXT_PUBLIC_BACKEND_URL` o `http://localhost:8000`) |
| `src/components/Header.tsx` · `Hero.tsx` · `FilterBar.tsx` | Cabecera corporativa, embudo de estado y barra de filtros en tiempo real |
| `src/components/MapView.tsx` · `LeafletMap.tsx` | Mapa interactivo de CCAA, buscador inteligente integrado y ranking territorial |
| `src/components/PlanView.tsx` | **Plan de ataque**: priorización por urgencia de cierre, seguimiento interno y próximos hitos |
| `src/components/PrevisionView.tsx` · `ProgramaDrawer.tsx` | **Previsión**: estimación de convocatorias recurrentes basada en histórico `2016+` y ficha de programa |
| `src/components/HistoricoView.tsx` | **Histórico**: archivo de convocatorias cerradas desde `2016`, desglose anual interactivo y búsqueda |
| `src/components/EmpresasView.tsx` | **Empresas**: convocatorias de fundaciones privadas/RSC (`privada_rsc`) con indicador de elegibilidad ESAL |
| `src/components/ConvocatoriaDrawer.tsx` | Ficha ejecutiva lateral con requisitos, financiación, enlace al documento oficial y exportación Markdown |
| `src/lib/search.ts` | Motor de búsqueda sin tildes con expansión bidireccional de siglas (`MITECO`, `OAPN`, `PEPAC`, `BDNS`, `PRTR`, etc.) |
| `src/lib/territorio.ts` · `recurrencia.ts` · `plazo.ts` · `novedades.ts` · `texto.ts` | Utilidades de filtrado geográfico, detección de programas cíclicos, cálculo de plazos y novedades |
| `public/data/ccaa.geojson` · `provincias.geojson` | Geometrías offline para renderizado del mapa sin dependencias externas |

---

## Arranque y Verificación

> En Windows con ExecutionPolicy restrictiva para scripts `.ps1`, utiliza **`npm.cmd`**.

```powershell
# Instalar dependencias
npm.cmd install

# Verificación de tipos TypeScript
.\node_modules\.bin\tsc.cmd --noEmit

# Compilación de producción (Turbopack)
npm.cmd run build

# Servir en producción (http://localhost:3000)
npm.cmd run start

# Modo desarrollo con recarga en caliente
npm.cmd run dev
```

### Variable de entorno opcional
Por defecto apunta al backend local en `http://localhost:8000`. Para apuntar a otro host:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```
