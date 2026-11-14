import { Convocatoria } from '@/types/convocatoria';
import { SIN_PLAZO } from '@/lib/plazo';

/** Días de antelación con los que conviene empezar a preparar una memoria (criterio del backend: 45 días). */
export const PREPARACION_PREVIA_DIAS = 45;

const DIA_MS = 86_400_000;
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
export const nombreMes = (m: number) => MESES[(m + 11) % 12];

export type Confianza = 'alta' | 'media' | 'baja';

export interface Programa {
  clave: string;
  nombre: string;
  organismo: string;
  ambito: string;
  /** Ediciones detectadas, de la más reciente a la más antigua */
  ediciones: Convocatoria[];
  anios: number[];
  /** Mes (1-12) en que suele publicarse */
  mesApertura: number;
  /** Duración típica de la ventana de solicitud, en días (null si no hay datos fiables) */
  ventanaDias: number | null;
  cuantiaMedia: number;
  confianza: Confianza;
  /** Edición abierta ahora, si la hay */
  abierta: Convocatoria | null;
  /** Próxima publicación prevista (tras la última edición detectada) */
  proxima: Date;
  /** Fecha a partir de la cual conviene empezar a preparar la solicitud */
  prepararDesde: Date;
  /** La fecha prevista ya pasó y no se ha detectado la edición de este año */
  retrasada: boolean;
}

const STOP = new Set([
  'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'en', 'a', 'al', 'para', 'por', 'con', 'se', 'que', 'su', 'sus', 'un', 'una', 'o',
  'convocatoria', 'convocatorias', 'convocan', 'bases', 'reguladoras', 'subvenciones', 'subvencion', 'ayudas', 'ayuda', 'concesion',
  'orden', 'resolucion', 'extracto', 'ejercicio', 'anio', 'ano', 'num', 'numero', 'regimen', 'concurrencia', 'competitiva', 'publica',
  'anual', 'anuales', 'primera', 'segunda', 'edicion', 'ii', 'iii', 'iv',
]);

const sinAcentos = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Identifica el «programa» al que pertenece una convocatoria: mismo órgano y mismo título sin años ni números de orden. */
export function claveDePrograma(c: Pick<Convocatoria, 'organismo' | 'titulo'>): string {
  const tema = sinAcentos(c.titulo)
    .replace(/\b(19|20)\d{2}(\s*[-/]\s*(19|20)?\d{2})?\b/g, ' ')
    .replace(/\b\d+[/.-]\d+\b/g, ' ')
    .replace(/[^a-z\s]/g, ' ')
    .split(/\s+/)
    .filter((p) => p.length > 2 && !STOP.has(p))
    .slice(0, 9)
    .join(' ');
  const org = sinAcentos(c.organismo).replace(/[^a-z\s]/g, ' ').split(/\s+/).filter((p) => p.length > 2 && !STOP.has(p)).slice(0, 4).join(' ');
  return `${org}|${tema}`;
}

const fecha = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`);

/** Distancia circular entre dos meses (0-6). */
const distMes = (a: number, b: number) => Math.min(Math.abs(a - b), 12 - Math.abs(a - b));

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

/**
 * Agrupa convocatorias (histórico + activas) en programas recurrentes y estima cuándo volverá a abrirse cada uno.
 * Un programa solo es «recurrente» si tiene ediciones en al menos 2 años distintos.
 * Método: mes de publicación más frecuente (moda) + regularidad (cuántas ediciones caen a ±1 mes) → confianza.
 */
export function detectarProgramas(todas: Convocatoria[], hoy: Date = new Date()): Programa[] {
  const grupos = new Map<string, Convocatoria[]>();
  for (const c of todas) {
    if (!c.fechaPublicacion || !c.titulo) continue;
    const k = claveDePrograma(c);
    if (k.length < 8) continue;
    grupos.set(k, [...(grupos.get(k) ?? []), c]);
  }

  const programas: Programa[] = [];
  grupos.forEach((eds, clave) => {
    const ediciones = [...eds].sort((a, b) => b.fechaPublicacion.localeCompare(a.fechaPublicacion));
    const anios = [...new Set(ediciones.map((c) => fecha(c.fechaPublicacion).getFullYear()))].sort((a, b) => a - b);
    if (anios.length < 2) return;

    // Una edición por año basta para estimar el mes: se toma la primera publicada de cada año
    const primeraDelAnio = anios.map((y) => [...ediciones].reverse().find((c) => fecha(c.fechaPublicacion).getFullYear() === y)!);
    const meses = primeraDelAnio.map((c) => fecha(c.fechaPublicacion).getMonth() + 1);
    const mes = moda(meses);
    const regularidad = meses.filter((m) => distMes(m, mes) <= 1).length / meses.length;
    const confianza: Confianza = anios.length >= 3 && regularidad >= 0.75 ? 'alta' : anios.length >= 2 && regularidad >= 0.5 ? 'media' : 'baja';

    const dia = mediana(primeraDelAnio.filter((c) => fecha(c.fechaPublicacion).getMonth() + 1 === mes).map((c) => fecha(c.fechaPublicacion).getDate()));
    const ventanas = ediciones
      .filter((c) => c.diasRestantes < SIN_PLAZO && c.fechaCierre > c.fechaPublicacion)
      .map((c) => Math.round((fecha(c.fechaCierre).getTime() - fecha(c.fechaPublicacion).getTime()) / DIA_MS))
      .filter((d) => d > 0 && d < 400);

    const abierta = ediciones.find((c) => c.estado === 'ACTIVA' || (c.estado === undefined && c.diasRestantes >= 0 && c.diasRestantes < SIN_PLAZO)) ?? null;

    // Próxima apertura: primer ciclo posterior a la última edición cuya fecha habitual no sea muy antigua.
    // Pasados 90 días se da por no repetida/no detectada y se salta al ciclo siguiente: avisar de un retraso
    // de meses sería ruido, sobre todo mientras la ingesta no cubra todas las fuentes.
    // Si ese ciclo ya pasó (hasta 90 días) y no hay edición detectada, se marca como «retrasada»:
    // debería haber salido y no consta, así que puede publicarse en cualquier momento.
    const ultimoAnio = anios[anios.length - 1];
    const limite = hoy.getTime() - 90 * DIA_MS;
    let proxima = new Date(ultimoAnio + 1, mes - 1, Math.min(dia, 28), 12);
    while (proxima.getTime() < limite) proxima = new Date(proxima.getFullYear() + 1, mes - 1, Math.min(dia, 28), 12);
    const retrasada = proxima.getTime() < hoy.getTime();

    const ref = ediciones[0];
    const cuantias = ediciones.map((c) => c.cuantiaMaximaProyecto).filter((n) => n > 0);
    programas.push({
      clave,
      nombre: ref.titulo,
      organismo: ref.organismo,
      ambito: ref.ambitoTerritorial,
      ediciones,
      anios,
      mesApertura: mes,
      ventanaDias: ventanas.length ? mediana(ventanas) : null,
      cuantiaMedia: cuantias.length ? Math.round(cuantias.reduce((a, b) => a + b, 0) / cuantias.length) : 0,
      confianza,
      abierta,
      proxima,
      prepararDesde: new Date(proxima.getTime() - PREPARACION_PREVIA_DIAS * DIA_MS),
      retrasada,
    });
  });

  return programas.sort((a, b) => a.proxima.getTime() - b.proxima.getTime());
}

/** Programas que previsiblemente se abrirán en los próximos `meses` meses (sin contar los ya abiertos). */
export function previstosEn(programas: Programa[], meses: number, hoy: Date = new Date()): Programa[] {
  const fin = new Date(hoy.getFullYear(), hoy.getMonth() + meses, hoy.getDate(), 12).getTime();
  return programas.filter((p) => !p.abierta && p.proxima.getTime() <= fin);
}

/** Texto corto de recurrencia para una convocatoria concreta (p. ej. en tarjetas de empresas). */
export function recurrenciaDe(c: Convocatoria, programas: Programa[]): Programa | undefined {
  const k = claveDePrograma(c);
  return programas.find((p) => p.clave === k);
}
