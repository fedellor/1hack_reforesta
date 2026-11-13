# 🌲 Radar Reforesta · Consola de Financiación y Decisión Territorial
> Proyecto desarrollado para el reto **1hack A Coruña — El reto de Reforesta**, impulsado por **Common Seeds (The Agile Monkeys)**.

[![Next.js](https://img.shields.io/badge/Next.js-16.4-black?logo=next.js)](https://nextjs.org/)
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

## 4. Vistas del Centro de Mando Frontend

La interfaz cuenta con 5 modos de visualización adaptados a la toma de decisiones:

* **📊 Fichas Inteligentes (Bandeja Ejecutiva):** Tarjetas horizontales de alta densidad con micro-barras de afinidad en las 3 líneas de Reforesta, badges financieros y citas clave.
* **📋 Tabla Técnica (Data Grid):** Vista compacta para escanear y ordenar decenas de oportunidades por cuantía, encaje o fecha de cierre en 1 clic.
* **📌 Pipeline Kanban:** Tablero de estados (*Nueva*, *Priorizada*, *En preparación*, *Presentada*, *Descartada*) para coordinar a las 6 personas del equipo sin pisarse el trabajo.
* **📅 Calendario de Deadlines:** Cronograma temporal agrupado por cercanía de cierre (&le;10d, 11-25d, &gt;25d) para planificar las entregas.
* **🗺️ Radar Territorial:** Mapa interactivo de España por Comunidades Autónomas con selección de ámbito estatal y selector de CCAA.
* **🏢 Canal Empresas RSC:** Pestaña dedicada a programas de patrocinio corporativo y fundaciones privadas (Santander ESG, ”la Caixa”) para romper la barrera del "canal a cero".

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
                   [ Fichas &amp; Tabla ]     [ Pipeline &amp; Mapa ]    [ Ficha Ejecutiva ]
```

* **Rama `front` (Frontend):** Aplicación Next.js ubicada en `/frontend` con tipado estricto, mock dinámico en `/api/convocatorias` y cliente de fallback automático a la API de backend.
* **Rama `back` (Backend):** Conectores a la API pública de la BDNS (`infosubvenciones.es`), boletines oficiales y extractor estructurado con LLM.

---

## 7. Instrucciones para Ejecutar el Proyecto en Local

### Requisitos previos
* Node.js v18+ (probado en v26)
* npm v9+

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
