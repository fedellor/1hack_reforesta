/** Códigos internos del radar → texto legible. */
const CODIGOS: Record<string, string> = {
  ONG_FUNDACIONES: 'ONG y fundaciones',
  AYUNTAMIENTO: 'ayuntamientos',
  COMUNIDAD_MONTES: 'comunidades de montes',
  EMPRESA_PYME: 'pymes',
  EMPRESA: 'empresas',
  UNIVERSIDAD: 'universidades',
  PERSONA_FISICA: 'personas físicas',
};

/** Temas del radar (sin acentos) → texto con ortografía. */
const TEMAS: [RegExp, string][] = [
  [/\bprevencion_incendios\b/g, 'prevención de incendios'],
  [/\bprevencion incendios\b/g, 'prevención de incendios'],
  [/\breforestacion\b/g, 'reforestación'],
  [/\brestauracion_ecologica\b/g, 'restauración ecológica'],
  [/\beducacion_ambiental\b/g, 'educación ambiental'],
  [/\bcustodia_territorio\b/g, 'custodia del territorio'],
  [/\bconservacion_habitats\b/g, 'conservación de hábitats'],
  [/\bbiodiversidad\b/g, 'biodiversidad'],
];

/** Quita códigos en bruto: ONG_FUNDACIONES, prevencion_incendios, pendiente_media… */
export function humanizar(texto: string | null | undefined): string {
  if (!texto) return '';
  let t = texto;
  for (const [codigo, legible] of Object.entries(CODIGOS)) t = t.split(codigo).join(legible);
  for (const [patron, legible] of TEMAS) t = t.replace(patron, legible);
  t = t.replace(/\(DIRECTA\)/g, '(relevancia directa)');
  // Códigos en mayúsculas con guion bajo (INDIRECTA_ELEGIBLE…) y en minúsculas (prevencion_incendios…)
  t = t.replace(/\b[A-Z]{3,}(?:_[A-Z]+)+\b/g, (m) => m.toLowerCase().replace(/_/g, ' '));
  return t.replace(/\b[a-z]+(?:_[a-z]+)+\b/g, (m) => m.replace(/_/g, ' '));
}

/** ¿Es una cita literal de las bases, o un texto generado por el radar? */
export function esCitaLiteral(texto: string): boolean {
  return !/^\s*\[[^\]]+\]/.test(texto) && !/Aprobada como/i.test(texto);
}

/** Limpia la justificación generada: sin etiquetas «[CÓDIGO]» y más corta. */
export function limpiarJustificacion(texto: string): string {
  let t = texto.replace(/^\s*(\[[^\]]+\]\s*)+/, '');
  const m = t.match(/actuaciones de (.+?) promovidas por/i);
  if (m) t = `Aborda directamente: ${m[1]}.`;
  return humanizar(t).trim();
}

const MINUSCULAS = new Set(['para', 'por', 'con', 'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'en', 'a', 'al', 'i', 'per', 'd', 'l']);
const SIGLAS = new Set(['mITECO', 'miteco', 'ue', 'boe', 'sl', 'sa', 'cyl']);

const aTitulo = (s: string) =>
  s
    .toLowerCase()
    .split(/(\s+|(?<=[-/(])|(?=[)/]))/)
    .map((p, i) => {
      const k = p.trim();
      if (!k || /^\W+$/.test(k)) return p;
      if (SIGLAS.has(k)) return p.toUpperCase();
      if (i > 0 && MINUSCULAS.has(k)) return p;
      return p.charAt(0).toUpperCase() + p.slice(1);
    })
    .join('');

/**
 * El backend envía el órgano con su clasificación interna y en mayúsculas
 * («AUTONOMICA - COMUNIDAD FORAL DE NAVARRA - DEPARTAMENTO DE…»). Se quita el prefijo y se pasa a mayúscula inicial.
 */
export function limpiarOrganismo(org: string | null | undefined): string {
  if (!org) return '';
  let t = org.replace(/^\s*(AUTONOMICA|AUTONÓMICA|LOCAL|ESTADO|OTROS|PROVINCIAL|MUNICIPAL)\s*-\s*/, '');
  const letras = t.replace(/[^A-Za-zÀ-ÿ]/g, '');
  const mayus = letras.replace(/[^A-ZÀ-Þ]/g, '').length;
  if (letras.length > 0 && mayus / letras.length > 0.7) t = aTitulo(t);
  return t.replace(/\s+/g, ' ').trim();
}
