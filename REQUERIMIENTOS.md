# 📋 Documento de Requisitos y Especificaciones del Proyecto
## Reto: 1hack A Coruña — El reto de Reforesta (Common Seeds)
### Plataforma: "Consola de Financiación Reforesta" (Radar Analítico y de Decisión)

---

## 1. Visión y Principio Rector del Producto

### 1.1 El Problema Específico de Reforesta
> *"Cada convocatoria que se le escapa a Reforesta es monte que no se planta."*

Reforesta (ONG de Utilidad Pública fundada en 1991, equipo de 6-7 personas) financia cada hectárea que restaura mediante subvenciones públicas o mecenazgo corporativo. Actualmente solo presentan **4 o 5 solicitudes al año** porque:
1. **Dispersión de fuentes:** Revisan solo 4 fuentes a mano (MITECO, Fundación Biodiversidad, CAM ambiental y Agenda 2030). Se les escapan cientos de convocatorias de diputaciones, CCAA, fondos europeos y empresas privadas (RSC).
2. **El "peaje de lectura" administrativo:** Para saber si una convocatoria encaja, una persona del equipo debe leerse decenas de páginas de bases legales en el BOE o boletines autonómicos. Muchas veces, tras 3 horas de lectura, descubren en la página 35 una cláusula de exclusión (*dealbreaker*) que invalida su candidatura.
3. **El canal de mecenazgo empresarial (RSC/ESG) está a cero:** Solo atienden a empresas que acuden a ellos por iniciativa propia.

### 1.2 Filosofía de la Plataforma: Máxima Densidad Informativa y Cero Pérdida de Tiempo
- ❌ **No es un buscador manual en el front:** El usuario no debe perder tiempo pensando qué palabras clave buscar o filtrando basura no aplicable.
- ❌ **No es un simple chatbot:** Un chat obliga al usuario a formular preguntas a ciegas y oculta la panorámica general.
- ❌ **El mapa no es el producto único:** El mapa es solo una vista o widget de apoyo territorial complementario.
- ✅ **El producto es un Radar Analítico y de Consulta:**
  - Una base de datos viva y proactiva donde la información ya está pre-procesada, clasificada y puntuada.
  - El frontend expone la **máxima información crítica masticada por convocatoria** para que el equipo de Reforesta estudie, consulte y decida si una oportunidad se solicita o se descarta.

---

## 2. Los 6 Datos Críticos que Resuelven el Dolor de Reforesta

Para cada oportunidad detectada, la plataforma debe condensar y mostrar de forma inmediata:

| Dato Crítico | Por qué le duele a Reforesta | Cómo lo visualiza la plataforma |
| :--- | :--- | :--- |
| **1. Semáforo de Elegibilidad (Dealbreakers)** | Es el mayor motivo de tiempo perdido: leer 40 páginas para descubrir que solo admiten PYMES, universidades o corporaciones locales. | 🟢 **Apta** (admite ONGs / entidades sin ánimo de lucro / Utilidad Pública / Custodia de Territorio)<br>🔴 **Excluida** (con el motivo explícito y cita de la cláusula). |
| **2. Finanzas y Cofinanciación** | Una ONG no tiene tesorería infinita. Si la ayuda requiere un 40% de cofinanciación propia, puede ser inasumible. | • Importe total de la convocatoria.<br>• Cuantía máxima por proyecto.<br>• **% de Cofinanciación exigida** (ej: *100% financiado* vs *Requiere 20% fondos propios*).<br>• Modalidad: ¿Anticipo de fondos o reembolso? |
| **3. Ventana de Oportunidad y Urgencia** | Fechas límites estrictas donde un día de retraso anula el trabajo. | • Fecha y hora de cierre.<br>• **Contador de días restantes** con código cromático (🔴 <7d, 🟡 <20d, 🟢 >20d). |
| **4. Matching Semántico Multidimensional (0–100%)** | Permite ordenar la bandeja de oportunidades de mayor a menor probabilidad de éxito. | Puntuación desglosada en las 3 líneas de Reforesta:<br>• **Restauración ecológica:** plantación autóctona, desertificación, charcas.<br>• **Conservación de hábitats:** tritones, ailanto, Guadarrama.<br>• **Educación ambiental:** voluntariado e inclusión.<br>*(Acompañado de **citas textuales de las bases** que lo justifican).* |
| **5. Acciones Subvencionables Directas** | Saber qué partidas de gasto reales les van a pagar antes de escribir nada. | Lista clara de conceptos cubiertos: compra de planta, desbroce, vallados protectores de fauna, jornales/nóminas, transporte, talleres escolares. |
| **6. Trazabilidad Oficial Inmutable** | Cero alucinaciones. El equipo necesita descargar las bases oficiales de inmediato. | Código BDNS oficial, enlace directo al PDF publicado en el boletín (BOE, BOCM, DOG...) y sede electrónica de tramitación. |

---

## 3. Arquitectura del Frontend (Next.js + Tailwind CSS)

### 3.1 Stack Tecnológico del Front (`rama: roi`)
- **Framework:** Next.js (App Router, TypeScript).
- **Estilos:** Tailwind CSS.
- **Componentes:** Shadcn UI / Radix Primitives + Lucide React (iconografía).
- **Mocks y Mock API Routes:** Endpoints en `/api/convocatorias` con datos reales tipados para iterar en la UI sin bloquearse si el backend está en desarrollo.

### 3.2 Vistas de Exploración y Decisión
- **Vista Principal: Fichas Enriquecidas / Data Grid Compacto:**
  - Visualización diferenciadora de alta densidad.
  - Cada elemento muestra badges de matching (3 líneas), importe, días restantes, ámbito territorial y la cita clave de las bases.
  - Filtros multifactor inmediatos: por CCAA, cuantía (€), urgencia (días) y nivel de afinidad (>80%).
- **Ficha Ejecutiva Desplegable (Slide-Over Drawer):**
  - Al seleccionar cualquier oportunidad, se abre un panel lateral sin perder la lista.
  - Contiene el resumen ejecutivo en lenguaje claro, requisitos de solvencia, desglose de gastos elegibles vs excluidos y botones de enlace directo al PDF y a la sede electrónica.
- **Vistas Complementarias:**
  - **Calendario / Cronograma de Deadlines:** Planificación de vencimientos temporales.
  - **Mapa Territorial Interactivo:** Widget visual para exploración geográfica por CCAA.
  - **Directorio de Mecenazgo RSC:** Oportunidades privadas de empresas y fundaciones bancarias.

---

## 4. Arquitectura del Pipeline y Backend (`rama: diego`)

- **Conexión en Vivo con APIs Públicas:**
  - BDNS (`infosubvenciones.es` / API de subvenciones del Estado).
  - Feeds de boletines oficiales (BOE, diarios autonómicos como BOCM y DOG).
- **Embudo en Dos Fases con LLM:**
  - *Fase 1 (Heurística de Metadatos):* Filtrado rápido por descriptor ambiental, fecha abierta y beneficiario general.
  - *Fase 2 (Extracción Quirúrgica LLM):* Análisis de artículos clave de las bases (objeto, beneficiarios, gastos) devolviendo un JSON con tipado estricto (Pydantic / Zod) con scoring multidimensional y citas literales.

---

## 5. Contrato de Datos Compartido (Data Contract / TypeScript Interface)

Para asegurar la sincronización perfecta entre el backend (`diego`) y el frontend (`roi`), los datos se estructuran con esta interfaz:

```typescript
export interface Convocatoria {
  id: string;
  codigoOficial: string;          // Ej: "BDNS 923290" u "Orden 1689/2026"
  titulo: string;
  organismo: string;              // Ej: "MITECO", "Comunidad de Madrid", "Fundación Santander"
  tipoFuente: 'publica_estatal' | 'publica_autonomica' | 'europea' | 'privada_rsc';
  ambitoTerritorial: string;      // "Estatal", "Madrid", "Galicia", etc.
  
  // Finanzas
  presupuestoTotal?: number;
  cuantiaMaximaProyecto: number;
  porcentajeCofinanciacion: number; // 0 significa 100% subvencionable
  modalidadPago: 'anticipo' | 'reembolso' | 'mixto';

  // Plazos
  fechaPublicacion: string;
  fechaCierre: string;
  diasRestantes: number;
  urgencia: 'critica' | 'moderada' | 'holgada'; // <7d, <20d, >20d

  // Elegibilidad y Scoring Reforesta
  elegible: boolean;
  motivoElegibilidad: string;     // Ej: "Apta: admite asociaciones sin ánimo de lucro declaradas de utilidad pública"
  dealbreakers: string[];         // Requisitos excluyentes detectados
  
  matchingGlobal: number;         // 0 - 100
  matchingLineas: {
    restauracionEcosistemas: number; // 0 - 100 (charcas, plantación, suelo)
    conservacionHabitats: number;    // 0 - 100 (tritón, ailanto, Guadarrama)
    educacionAmbiental: number;      // 0 - 100 (voluntariado, sensibilización)
  };
  citasBasesJustificacion: string[]; // Frases literales extraídas del PDF

  // Contenido de la Ficha Ejecutiva
  resumenEjecutivo: string;
  accionesSubvencionables: string[];
  gastosNoSubvencionables?: string[];
  requisitosSolvencia?: string[];

  // Trazabilidad
  urlBasesPdf: string;
  urlSedeElectronica: string;
  fuenteUrl: string;

  // Estado Interno Reforesta
  estadoInterno: 'nueva' | 'priorizada' | 'en_preparacion' | 'presentada' | 'descartada';
}
```

---

## 6. Hoja de Ruta para la Rama `roi` (Frontend)

1. **Paso 1:** Inicializar la aplicación Next.js con Tailwind CSS y TypeScript en el workspace.
2. **Paso 2:** Crear el archivo de tipos (`types/convocatoria.ts`) y un mock estructurado con las convocatorias reales del reto (*Orden 1689/2026 CAM*, *BDNS 923290 MITECO*, *Fondo RSC Santander*).
3. **Paso 3:** Desarrollar los componentes nucleares de la UI:
   - Header con métricas de impacto consolidadas.
   - Barra de filtros rápidos (CCAA, cuantía, plazo, % match).
   - Vista de listado/tarjetas enriquecidas con barras de afinidad.
   - Panel lateral desplegable (*Drawer*) para la Ficha Ejecutiva Completa.
4. **Paso 4:** Desarrollar las vistas complementarias (Calendario de deadlines y Widget de Mapa).
5. **Paso 5:** Conectar la llamada de datos (lista para cambiar de mock local a la API en vivo de Diego con una sola variable de entorno `NEXT_PUBLIC_API_URL`).
