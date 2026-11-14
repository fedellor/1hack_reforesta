import { Convocatoria } from '@/types/convocatoria';
import { SIN_PLAZO } from '@/lib/plazo';

/** Días de antelación con los que conviene empezar a preparar una memoria (criterio del backend: 45 días). */
export const PREPARACION_PREVIA_DIAS = 45;

/**
 * Parecido mínimo entre dos títulos (índice de Jaccard sobre sus palabras) para considerar que son el mismo programa.
 * Con valores altos un programa se parte cuando el título cambia ligeramente de un año a otro; con valores bajos se mezclan
 * programas distintos del mismo órgano. 0,55 es un punto prudente; se puede contrastar con `evaluarPrevision`.
 */
export const UMBRAL_AGRUPADO = 0.55;

const DIA_MS = 86_400_000;

/** Máxima amplitud de la ventana habitual de apertura, en meses. */
const VENTANA_MAXIMA_MESES = 3;
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
export const nombreMes = (m: number) => MESES[(m + 11) % 12];

/**
 * Probabilidad de que el programa salga en su próximo ciclo, por reglas simples (medidas con el histórico, ver `evaluarPrevision`):
 * - alta: salió el año anterior al ciclo y tiene 3 o más años de edición.
 * - media: salió el año anterior al ciclo, pero solo tiene 2 años de edición.
 * - baja: lleva 2 o más años sin salir.
 * La regularidad del mes NO entra aquí: sirve para estimar cuándo, no si.
 */
export type Tramo = 'alta' | 'media' | 'baja';

export const ETIQUETA_TRAMO: Record<Tramo, string> = { alta: 'Alta', media: 'Media', baja: 'Baja' };
export const ORDEN_TRAMO: Record<Tramo, number> = { alta: 0, media: 1, baja: 2 };

/** Ventana habitual en texto: «marzo» o «marzo – mayo». */
export const textoVentana = (p: Pick<Programa, 'mesDesde' | 'mesHasta'>) =>
  p.mesDesde === p.mesHasta ? nombreMes(p.mesDesde) : `${nombreMes(p.mesDesde)} – ${nombreMes(p.mesHasta)}`;

export interface Programa {
  clave: string;
  nombre: string;
  organismo: string;
  ambito: string;
  /** Ediciones detectadas, de la más reciente a la más antigua */
  ediciones: Convocatoria[];
  anios: number[];
  /** Mes (1-12) en que más veces se ha publicado */
  mesApertura: number;
  /** Ventana habitual de publicación: arco de meses más corto que contiene todas las ediciones (circular, 1-12) */
  mesDesde: number;
  mesHasta: number;
  /** Las ediciones salieron en meses muy distintos: la ventana se centra en el mes más habitual y es menos fiable */
  dispersa: boolean;
  /** Duración típica de la ventana de solicitud, en días (null si no hay datos fiables) */
  ventanaDias: number | null;
  cuantiaMedia: number;
  tramo: Tramo;
  /** Edición abierta ahora, si la hay */
  abierta: Convocatoria | null;
  /** Primer día de la ventana prevista del próximo ciclo */
  proxima: Date;
  /** Último día de la ventana prevista */
  proximaFin: Date;
  /** Fecha a partir de la cual conviene empezar a preparar la solicitud (45 días antes del inicio de la ventana) */
  prepararDesde: Date;
  /** Hoy estamos dentro de la ventana prevista y no se ha detectado la edición: puede salir ya */
  enVentana: boolean;
  /** La ventana prevista terminó hace poco y no se ha detectado la edición de este ciclo */
  retrasada: boolean;
}

const STOP = new Set([
  'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'en', 'a', 'al', 'para', 'por', 'con', 'se', 'que', 'su', 'sus', 'un', 'una', 'o',
  'convocatoria', 'convocatorias', 'convocan', 'bases', 'reguladoras', 'subvenciones', 'subvencion', 'ayudas', 'ayuda', 'concesion',
  'orden', 'resolucion', 'extracto', 'ejercicio', 'anio', 'ano', 'num', 'numero', 'regimen', 'concurrencia', 'competitiva', 'publica',
  'anual', 'anuales', 'primera', 'segunda', 'edicion', 'ii', 'iii', 'iv',
]);

const sinAcentos = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Palabras significativas del título, sin años, números de orden ni palabras vacías. */
function tokensTema(titulo: string): Set<string> {
  return new Set(
    sinAcentos(titulo)
      .replace(/\b(19|20)\d{2}(\s*[-/]\s*(19|20)?\d{2})?\b/g, ' ')
      .replace(/\b\d+[/.-]\d+\b/g, ' ')
      .replace(/[^a-z\s]/g, ' ')
      .split(/\s+/)
      .filter((p) => p.length > 3 && !STOP.has(p))
  );
}

/** Órgano convocante, reducido a sus palabras principales. */
function claveOrganismo(organismo: string): string {
  return sinAcentos(organismo)
    .replace(/[^a-z\s]/g, ' ')
    .split(/\s+/)
    .filter((p) => p.length > 2 && !STOP.has(p))
    .slice(0, 4)
    .join(' ');
}

function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let comunes = 0;
  a.forEach((w) => b.has(w) && comunes++);
  return comunes / (a.size + b.size - comunes);
}

/**
 * Agrupa convocatorias en programas: mismo órgano y títulos suficientemente parecidos (enlace por cadena: si A se parece
 * a B y B a C, los tres son el mismo programa, lo que tolera que el título evolucione poco a poco).
 */
function agrupar(todas: Convocatoria[]): Convocatoria[][] {
  const porOrgano = new Map<string, { c: Convocatoria; t: Set<string> }[]>();
  for (const c of todas) {
    if (!c.fechaPublicacion || !c.titulo) continue;
    const t = tokensTema(c.titulo);
    if (t.size === 0) continue;
    const k = claveOrganismo(c.organismo);
    porOrgano.set(k, [...(porOrgano.get(k) ?? []), { c, t }]);
  }
  const grupos: Convocatoria[][] = [];
  porOrgano.forEach((items) => {
    const padre = items.map((_, i) => i);
    const raiz = (x: number): number => (padre[x] === x ? x : (padre[x] = raiz(padre[x])));
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        if (jaccard(items[i].t, items[j].t) >= UMBRAL_AGRUPADO) padre[raiz(i)] = raiz(j);
      }
    }
    const g = new Map<number, Convocatoria[]>();
    items.forEach((it, i) => g.set(raiz(i), [...(g.get(raiz(i)) ?? []), it.c]));
    g.forEach((v) => grupos.push(v));
  });
  return grupos;
}

const fecha = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`);

function moda(valores: number[]): number {
  const cuenta = new Map<number, number>();
  valores.forEach((v) => cuenta.set(v, (cuenta.get(v) ?? 0) + 1));
  let mejor = valores[0];
  let max = 0;
  cuenta.forEach((n, v) => {
    if (n > max || (n === max && v > mejor)) {
      mejor = v;
      max = n;
    }
  });
  return mejor;
}

const mediana = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2);
};

/** Arco circular más corto de meses (1-12) que contiene todos los dados: p. ej. [12, 1, 1] → de diciembre a enero. */
export function arcoDeMeses(meses: number[]): { desde: number; hasta: number } {
  const unicos = [...new Set(meses)].sort((a, b) => a - b);
  if (unicos.length === 1) return { desde: unicos[0], hasta: unicos[0] };
  // El arco empieza justo después del mayor hueco entre meses consecutivos (contando el salto de diciembre a enero)
  let mejorHueco = -1;
  let desde = unicos[0];
  for (let i = 0; i < unicos.length; i++) {
    const actual = unicos[i];
    const siguiente = unicos[(i + 1) % unicos.length];
    const hueco = (siguiente - actual + 12) % 12;
    if (hueco > mejorHueco) {
      mejorHueco = hueco;
      desde = siguiente;
    }
  }
  const hasta = ((desde + (12 - mejorHueco) - 1) % 12) + 1;
  return { desde, hasta: hasta === 0 ? 12 : hasta };
}

/** ¿El mes (1-12) cae dentro del arco [desde, hasta] ampliado en `margen` meses por cada lado? */
export function mesEnArco(mes: number, desde: number, hasta: number, margen = 0): boolean {
  const largo = ((hasta - desde + 12) % 12) + 1;
  const pos = (mes - desde + 12) % 12;
  return pos < largo || pos < largo + margen || (desde - mes + 12) % 12 <= margen;
}

/**
 * Agrupa convocatorias (histórico + activas) en programas recurrentes y estima cuándo volverá a abrirse cada uno.
 * Un programa solo es «recurrente» si tiene ediciones en al menos 2 años distintos.
 * - Si saldrá: tramo por reglas simples (recencia y años con edición).
 * - Cuándo: ventana de meses en que ha salido históricamente.
 */
export function detectarProgramas(todas: Convocatoria[], hoy: Date = new Date()): Programa[] {
  const programas: Programa[] = [];
  for (const eds of agrupar(todas)) {
    const ediciones = [...eds].sort((a, b) => b.fechaPublicacion.localeCompare(a.fechaPublicacion));
    const anios = [...new Set(ediciones.map((c) => fecha(c.fechaPublicacion).getFullYear()))].sort((a, b) => a - b);
    if (anios.length < 2) continue;

    // Una edición por año basta para estimar el mes: se toma la primera publicada de cada año
    const primeraDelAnio = anios.map((y) => [...ediciones].reverse().find((c) => fecha(c.fechaPublicacion).getFullYear() === y)!);
    const meses = primeraDelAnio.map((c) => fecha(c.fechaPublicacion).getMonth() + 1);
    const mes = moda(meses);
    // Ventana habitual: el arco más corto que contiene todas las ediciones; si se dispersa (más de 3 meses) se centra en el mes
    // más habitual, ±1. Medido con el histórico, una ventana de 5-8 meses «acierta» casi siempre pero no dice nada útil.
    const arco = arcoDeMeses(meses);
    const dispersa = ((arco.hasta - arco.desde + 12) % 12) + 1 > VENTANA_MAXIMA_MESES;
    const desde = dispersa ? ((mes + 10) % 12) + 1 : arco.desde;
    const hasta = dispersa ? (mes % 12) + 1 : arco.hasta;

    const diasEnDesde = primeraDelAnio.filter((c) => fecha(c.fechaPublicacion).getMonth() + 1 === desde).map((c) => fecha(c.fechaPublicacion).getDate());
    const dia = diasEnDesde.length ? mediana(diasEnDesde) : 1; // si la ventana se centró en la moda puede no haber ediciones en su primer mes
    const ventanas = ediciones
      .filter((c) => c.diasRestantes < SIN_PLAZO && c.fechaCierre > c.fechaPublicacion)
      .map((c) => Math.round((fecha(c.fechaCierre).getTime() - fecha(c.fechaPublicacion).getTime()) / DIA_MS))
      .filter((d) => d > 0 && d < 400);

    const abierta = ediciones.find((c) => c.estado === 'ACTIVA' || (c.estado === undefined && c.diasRestantes >= 0 && c.diasRestantes < SIN_PLAZO)) ?? null;

    // Próximo ciclo: el primero posterior a la última edición cuya ventana no terminó hace más de 90 días. Si la ventana
    // ya terminó hace menos de 90 días y no hay edición, se marca «retrasada»; pasado ese plazo se da por no repetida o
    // no detectada y se salta al ciclo siguiente (avisar de un retraso de meses sería ruido mientras la ingesta sea parcial).
    const ultimoAnio = anios[anios.length - 1];
    const cruza = desde > hasta; // la ventana atraviesa el cambio de año (p. ej. diciembre-enero)
    const ventanaDeCiclo = (ciclo: number) => ({
      inicio: new Date(ciclo, desde - 1, Math.min(dia, 28), 12),
      fin: new Date(cruza ? ciclo + 1 : ciclo, hasta, 0, 12), // último día del mes «hasta»
    });
    let ciclo = ultimoAnio + 1;
    let v = ventanaDeCiclo(ciclo);
    while (v.fin.getTime() < hoy.getTime() - 90 * DIA_MS) {
      ciclo++;
      v = ventanaDeCiclo(ciclo);
    }
    const enVentana = hoy.getTime() >= v.inicio.getTime() && hoy.getTime() <= v.fin.getTime();
    const retrasada = hoy.getTime() > v.fin.getTime();

    const tramo: Tramo = ciclo - ultimoAnio <= 1 ? (anios.length >= 3 ? 'alta' : 'media') : 'baja';

    const ref = ediciones[0];
    const cuantias = ediciones.map((c) => c.cuantiaMaximaProyecto).filter((n) => n > 0);
    programas.push({
      clave: `${claveOrganismo(ref.organismo)}|${ediciones.map((c) => c.id).sort()[0]}`,
      nombre: ref.titulo,
      organismo: ref.organismo,
      ambito: ref.ambitoTerritorial,
      ediciones,
      anios,
      mesApertura: mes,
      mesDesde: desde,
      mesHasta: hasta,
      dispersa,
      ventanaDias: ventanas.length ? mediana(ventanas) : null,
      cuantiaMedia: cuantias.length ? Math.round(cuantias.reduce((a, b) => a + b, 0) / cuantias.length) : 0,
      tramo,
      abierta,
      proxima: v.inicio,
      proximaFin: v.fin,
      prepararDesde: new Date(v.inicio.getTime() - PREPARACION_PREVIA_DIAS * DIA_MS),
      enVentana: enVentana && !abierta,
      retrasada: retrasada && !abierta,
    });
  }
  return programas.sort((a, b) => a.proxima.getTime() - b.proxima.getTime());
}

/** Solo tiene sentido prever lo que Reforesta podría pedir: alguna edición anterior fue apta. */
export const esAccionable = (p: Programa) => p.ediciones.some((c) => c.elegible);

/** Programas que previsiblemente se abrirán en los próximos `meses` meses (sin contar los ya abiertos). */
export function previstosEn(programas: Programa[], meses: number, hoy: Date = new Date()): Programa[] {
  const fin = new Date(hoy.getFullYear(), hoy.getMonth() + meses, hoy.getDate(), 12).getTime();
  return programas.filter((p) => !p.abierta && p.proxima.getTime() <= fin);
}

/** Programa recurrente al que pertenece una convocatoria concreta (p. ej. para mostrar «se repite» en las tarjetas de empresas). */
export function recurrenciaDe(c: Convocatoria, programas: Programa[]): Programa | undefined {
  return programas.find((p) => p.ediciones.some((e) => e.id === c.id));
}

/** ¿Esta convocatoria es una edición del programa? (mismo órgano y título parecido a alguna edición conocida) */
function esEdicionDe(p: Programa, c: Convocatoria): boolean {
  if (claveOrganismo(c.organismo) !== claveOrganismo(p.organismo)) return false;
  const t = tokensTema(c.titulo);
  return p.ediciones.some((e) => jaccard(tokensTema(e.titulo), t) >= UMBRAL_AGRUPADO);
}

export interface AciertoTramo {
  /** Previsiones hechas */
  n: number;
  /** Cuántas se cumplieron: salió una edición en el año previsto */
  enAnio: number;
  /** De las que salieron, en cuántas el mes cayó dentro de la ventana prevista (≤ 3 meses, sin margen) */
  mesEnVentana: number;
}

export interface Evaluacion {
  /** Años evaluados (cada uno se predice usando solo lo ocurrido en años anteriores) */
  anios: number[];
  total: AciertoTramo;
  porTramo: Record<Tramo, AciertoTramo>;
}

/**
 * Comprueba el método con el propio histórico (backtesting): para cada año completo se hace la previsión con lo que se
 * sabía a 1 de enero y se compara con lo que salió. Se recalcula con los datos cargados, así que mide lo que hay en cada
 * momento. Ojo: el histórico solo contiene lo que el radar ha capturado; si faltan convocatorias, el acierto real es mayor.
 */
export function evaluarPrevision(todas: Convocatoria[], hoy: Date = new Date()): Evaluacion {
  const anioDe = (c: Convocatoria) => fecha(c.fechaPublicacion).getFullYear();
  const validas = todas.filter((c) => c.fechaPublicacion && c.titulo && c.estado === 'CERRADA');
  const vacio = (): AciertoTramo => ({ n: 0, enAnio: 0, mesEnVentana: 0 });
  const ev: Evaluacion = { anios: [], total: vacio(), porTramo: { alta: vacio(), media: vacio(), baja: vacio() } };
  if (validas.length === 0) return ev;

  const minimo = Math.min(...validas.map(anioDe));
  // Hacen falta al menos 2 años de historia para prever, y el año evaluado debe haber terminado
  for (let y = minimo + 2; y < hoy.getFullYear(); y++) {
    const corte = new Date(y, 0, 1, 12);
    const pasado = todas.filter((c) => c.fechaPublicacion && anioDe(c) < y);
    const delAnio = todas.filter((c) => c.fechaPublicacion && anioDe(c) === y);
    const previstos = previstosEn(detectarProgramas(pasado, corte), 12, corte).filter((p) => p.proxima.getFullYear() === y && esAccionable(p));
    if (previstos.length === 0) continue;
    ev.anios.push(y);
    for (const p of previstos) {
      const salidas = delAnio.filter((c) => esEdicionDe(p, c));
      const enAnio = salidas.length > 0;
      const enVentana = salidas.some((c) => mesEnArco(fecha(c.fechaPublicacion).getMonth() + 1, p.mesDesde, p.mesHasta, 0));
      for (const t of [ev.total, ev.porTramo[p.tramo]]) {
        t.n++;
        if (enAnio) t.enAnio++;
        if (enAnio && enVentana) t.mesEnVentana++;
      }
    }
  }
  return ev;
}
