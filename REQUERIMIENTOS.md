# Requisitos del proyecto

**Reto:** 1hack A Coruña — el reto de Reforesta (Common Seeds). **Producto:** Radar Reforesta, una consola interna de financiación.

---

## 1. El problema

> *«Cada convocatoria que se le escapa a Reforesta es monte que no se planta.»*

Reforesta (ONG de Utilidad Pública fundada en 1991, equipo de 6–7 personas) financia cada hectárea que restaura con subvenciones públicas o mecenazgo. Hoy presenta **4 o 5 solicitudes al año** porque:

1. **Fuentes dispersas.** Revisa a mano solo cuatro (MITECO, Fundación Biodiversidad, CAM ambiental y Agenda 2030). Se le escapan convocatorias de diputaciones, comunidades, fondos europeos y empresas.
2. **Peaje de lectura.** Para saber si una convocatoria encaja hay que leer decenas de páginas de bases. A menudo, tras horas de lectura, aparece en la página 35 una cláusula que la excluye.
3. **Canal de mecenazgo empresarial sin atender.** Solo responde a empresas que se acercan por iniciativa propia.

## 2. Cómo se resuelve

El producto es un **radar de consulta**, no un buscador manual ni un chatbot. La información llega ya procesada, clasificada y puntuada, y el equipo decide si pide o descarta. El mapa es una vista de apoyo.

Para cada convocatoria, la plataforma resuelve seis datos:

| Dato | Qué evita | Cómo se muestra |
| :--- | :--- | :--- |
| **Elegibilidad** | Leer 40 páginas para descubrir que solo admiten pymes o ayuntamientos | Apta o excluida, con el motivo y los requisitos excluyentes |
| **Importe** | Perder tiempo en ayudas inasumibles | Importe máximo por proyecto; las licitaciones se marcan como tales y no suman como fondos |
| **Plazo y urgencia** | Perder una convocatoria por un día | Fecha de cierre y días restantes, con color por urgencia |
| **Afinidad (0–100 %)** | Ordenar a ciegas | Puntuación con las tres líneas de Reforesta: restauración, hábitats y educación ambiental |
| **Qué se paga** | Escribir sin saber qué cubre | Gastos subvencionables, cuando la convocatoria los concreta |
| **Trazabilidad** | Datos sin origen | Código oficial y enlace a la convocatoria oficial |

Los datos que las fuentes no traen (cofinanciación, modalidad de pago, orografía) **no se inventan ni se rellenan con valores por defecto**.

## 3. Qué ofrece la web

Interna, sin secciones públicas, solo con datos reales:

- **Mapa:** reparto territorial y buscador.
- **Plan de ataque:** cierres por mes, pensados para la urgencia.
- **Empresas:** fundaciones y mecenazgo.
- **Previsión:** lo que suele salir cada mes, según el histórico, con la medición de su acierto.
- **Histórico:** archivo de convocatorias cerradas, con filtros.
- **Ficha** de cada convocatoria, con el botón de convocatoria oficial.
- **Informe semanal** de novedades, en HTML o PDF.

## 4. Backend

- **Fuentes en vivo:** BDNS, BOE, TED y PLACSP, UE (SEDIA), 19 boletines autonómicos y fundaciones, más los PDF de `fuentes/`.
- **Filtro en dos capas:** reglas deterministas y, después, clasificación asistida por IA o motor local si no hay clave.
- **Elegibilidad según los estatutos de Reforesta**, con los requisitos excluyentes detectados.
- **Sincronización diaria a las 07:00** (Europe/Madrid), con recuperación al arrancar.
- Diseño detallado en [PLAN_PROYECTO.md](PLAN_PROYECTO.md).

## 5. Contrato de datos

El backend sirve cada convocatoria en el formato de `frontend/src/types/convocatoria.ts` (`GET /api/convocatorias`). Campos principales:

| Grupo | Campos |
| :--- | :--- |
| Identificación | `id`, `codigoOficial`, `titulo`, `organismo`, `tipoFuente` (`publica_estatal`, `publica_autonomica`, `europea`, `privada_rsc`), `ambitoTerritorial` |
| Dinero | `presupuestoTotal`, `cuantiaMaximaProyecto` |
| Plazos | `fechaPublicacion`, `fechaCierre`, `diasRestantes`, `urgencia`, `estado` (`ACTIVA`, `PROXIMA`, `CERRADA`) |
| Elegibilidad | `elegible`, `motivoElegibilidad`, `dealbreakers`, `matchingGlobal`, `matchingLineas`, `citasBasesJustificacion` |
| Contenido | `resumenEjecutivo`, `accionesSubvencionables`, `requisitosSolvencia` |
| Trazabilidad | `urlBasesPdf`, `urlSedeElectronica`, `fuenteUrl` |

## 6. Estado frente al reto

| Objetivo | Estado |
| :--- | :--- |
| Ir más allá de las 4 fuentes manuales | Hecho: 7 familias de fuentes, sincronizadas a diario |
| Evitar leer las bases enteras | Hecho en parte: veredicto, requisitos excluyentes y citas. La regla de elegibilidad del backend es laxa y deja pasar convocatorias que no encajan |
| Activar el canal de mecenazgo | Parcial: sección Empresas con pocas fundaciones, porque los conectores leen portadas y no programas concretos |
| Anticipar convocatorias | Hecho: Previsión con acierto medido (alta: 63 %, 20 de 32 casos) |
| Herramienta interna | Hecho |
| Informe periódico por correo | Informe hecho; el envío automático está pendiente |

Pendiente para producción: autenticación en los endpoints de administración, HTTPS, copias de seguridad y más histórico.
