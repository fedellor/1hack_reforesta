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
