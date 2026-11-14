import { Convocatoria } from '@/types/convocatoria';

const STOPWORDS_ES = new Set([
  'a',
  'al',
  'con',
  'de',
  'del',
  'e',
  'el',
  'en',
  'la',
  'las',
  'lo',
  'los',
  'o',
  'para',
  'por',
  'su',
  'sus',
  'u',
  'un',
  'una',
  'unas',
  'unos',
  'y',
]);

/**
 * Grupos estrictamente equivalentes (bidireccionales): cualquier término del grupo
 * expande al resto del grupo. Los acrónimos cortos (<= 3 letras) solo se activan
 * y comparan por palabra exacta.
 */
const GRUPOS_EQUIVALENTES: string[][] = [
  [
    'miteco',
    'ministerio para la transicion ecologica',
    'transicion ecologica y el reto demografico',
    'orden ted',
    'secretaria de estado de medio ambiente',
    'direccion general de biodiversidad bosques y desertificacion',
    'magrama',
    'mapama',
  ],
  [
    'oapn',
    'organismo autonomo parques nacionales',
  ],
  [
    'pepac',
    'plan estrategico de la pac',
    'feader',
  ],
  [
    'prtr',
    'nextgeneration',
    'next generation',
    'plan de recuperacion transformacion y resiliencia',
    'mrr',
  ],
  [
    'placsp',
    'perfil del contratante',
    'contratacion del sector publico',
  ],
  [
    'boe',
    'boletin oficial del estado',
  ],
  [
    'bocm',
    'boletin oficial de la comunidad de madrid',
  ],
  [
    'xunta',
    'xunta de galicia',
  ],
  [
    'jcyl',
    'junta de castilla y leon',
  ],
  [
    'jccm',
    'junta de comunidades de castilla la mancha',
  ],
  [
    'gva',
    'generalitat valenciana',
    'comunitat valenciana',
  ],
  [
    'dga',
    'gobierno de aragon',
  ],
  [
    'ue',
    'union europea',
    'europa',
    'europea',
    'programa life',
    'horizon europe',
    'interreg',
    'feder',
  ],
  [
    'anticipo',
    'pago anticipado',
    'sin aval',
  ],
  [
    'incendios',
    'incendio',
    'postincendio',
    'post incendio',
    'cortafuegos',
  ],
  [
    'selvicultura',
    'silvicultura',
    'selvicola',
    'silvicola',
  ],
  [
    'cataluna',
    'catalunya',
  ],
  [
    'illes balears',
    'islas baleares',
    'baleares',
  ],
  [
    'pais vasco',
    'euskadi',
  ],
];

/**
 * Expansiones unidireccionales desde el término buscado por el usuario hacia
 * conceptos equivalentes en los expedientes (evita contaminar palabras genéricas
 * como "fundacion" cuando se busca "fundacion biodiversidad").
 */
const EXPANSIONES_ORIGEN: Record<string, string[]> = {
  ong: ['ong', 'esal', 'sin animo de lucro', 'tercer sector', 'utilidad publica', 'asociacion', 'fundacion'],
  esal: ['esal', 'ong', 'sin animo de lucro', 'tercer sector', 'utilidad publica', 'asociacion', 'fundacion'],
  'tercer sector': ['tercer sector', 'sin animo de lucro', 'ong', 'esal', 'utilidad publica'],
  fb: ['fb', 'fundacion biodiversidad'],
  empleaverde: ['empleaverde', 'fundacion biodiversidad'],
  pleamar: ['pleamar', 'fundacion biodiversidad'],
  cam: ['cam', 'comunidad de madrid', 'bocm'],
  galicia: ['galicia', 'xunta'],
  aragon: ['aragon', 'dga', 'gobierno de aragon'],
  valenciana: ['valenciana', 'comunitat valenciana', 'comunidad valenciana', 'gva', 'generalitat valenciana'],
  valencia: ['valencia', 'comunitat valenciana', 'comunidad valenciana', 'gva', 'generalitat valenciana'],
  reforestacion: ['reforest', 'repobl', 'plantacion', 'restauracion forestal', 'selvic', 'silvic', 'masas forestales'],
  reforestar: ['reforest', 'repobl', 'plantacion', 'restauracion forestal', 'selvic', 'silvic'],
  repoblacion: ['repobl', 'reforest', 'restauracion forestal'],
  licitacion: ['licita', 'placsp', 'contrato'],
  licitaciones: ['licita', 'placsp', 'contrato'],
  subvencion: ['subvenc', 'bdns', 'ayuda'],
  subvenciones: ['subvenc', 'bdns', 'ayuda'],
  estatal: ['estatal', 'nacional', 'administracion general del estado'],
  '100%': ['100%', 'sin cofinanciacion', 'financiado al 100'],
};

/**
 * Normaliza texto eliminando tildes/diacríticos, pasando a minúsculas y
 * sustituyendo separadores (-, /, ., _, etc.) por espacios simples.
 */
export function normalizarTexto(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9%]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function compactarCodigo(texto: string): string {
  return normalizarTexto(texto).replace(/\s+/g, '');
}

/**
 * Tokeniza la consulta preservando términos significativos y manteniendo
 * palabras vacías solo si la consulta no tiene otros términos.
 */
export function tokenizarConsulta(consulta: string): string[] {
  const norm = normalizarTexto(consulta);
  if (!norm) return [];
  const rawTokens = norm.split(' ').filter(Boolean);
  const significativos = rawTokens.filter((t) =>
    t.length > 2 ? !STOPWORDS_ES.has(t) : !STOPWORDS_ES.has(t) || rawTokens.length === 1
  );
  return significativos.length > 0 ? significativos : rawTokens;
}

function variantesToken(token: string): string[] {
  const out = new Set<string>([token]);
  if (token.length >= 6 && token.endsWith('es')) {
    out.add(token.slice(0, -2));
  }
  if (token.length >= 5 && token.endsWith('s') && !token.endsWith('es')) {
    out.add(token.slice(0, -1));
  }
  if (token.startsWith('reforest') && token.length >= 8) {
    out.add('reforest');
  }
  if (token.startsWith('repobl') && token.length >= 6) {
    out.add('repobl');
  }
  if (token.startsWith('subvenc') && token.length >= 7) {
    out.add('subvenc');
  }
  if (token.startsWith('licita') && token.length >= 6) {
    out.add('licita');
  }
  if (token.startsWith('selvic') || token.startsWith('silvic')) {
    out.add('selvic');
    out.add('silvic');
  }
  return Array.from(out);
}

function expandirCandidatosToken(token: string, consultaNorm: string): string[] {
  const tokVars = variantesToken(token);
  const exactos = new Set<string>(tokVars);
  const sinonimos = new Set<string>();

  for (const v of tokVars) {
    if (EXPANSIONES_ORIGEN[v]) {
      for (const exp of EXPANSIONES_ORIGEN[v]) {
        sinonimos.add(exp);
      }
    }
  }
  if (EXPANSIONES_ORIGEN[consultaNorm]) {
    for (const exp of EXPANSIONES_ORIGEN[consultaNorm]) {
      sinonimos.add(exp);
    }
  }

  for (const grupo of GRUPOS_EQUIVALENTES) {
    const grupoCoincide = grupo.some((frase) => {
      if (frase.length <= 3) {
        return tokVars.includes(frase) || consultaNorm === frase;
      }
      if (frase.includes(' ')) {
        return consultaNorm.includes(frase);
      }
      return tokVars.some((v) => frase === v);
    });

    if (grupoCoincide) {
      for (const frase of grupo) {
        sinonimos.add(frase);
      }
    }
  }

  return Array.from(new Set([...exactos, ...sinonimos]));
}

interface CamposIndexados {
  codigo: string;
  codigoCompacto: string;
  titulo: string;
  organismo: string;
  territorio: string;
  detalles: string;
  fondo: string;
}

function textoCoincideConTermino(
  texto: string,
  palabrasSet: Set<string>,
  termino: string,
  compacto?: string
): boolean {
  if (!termino) return false;
  if (termino.length <= 3) {
    return palabrasSet.has(termino);
  }
  if (texto.includes(termino)) {
    return true;
  }
  if (compacto && termino.length >= 5 && compacto.includes(termino.replace(/\s+/g, ''))) {
    return true;
  }
  return false;
}

function construirCampos(c: Convocatoria): CamposIndexados {
  const metaExtra: string[] = [];
  if (c.porcentajeCofinanciacion === 0) {
    metaExtra.push('100% financiado sin cofinanciacion');
  }
  if (c.modalidadPago === 'anticipo' || c.pagoAnticipadoSinAval) {
    metaExtra.push('anticipo pago anticipado sin aval');
  }
  if (c.id.startsWith('bdns-')) {
    metaExtra.push('bdns subvencion ayudas');
  }
  if (c.id.startsWith('placsp-')) {
    metaExtra.push('placsp licitacion contrato publico perfil del contratante');
  }
  if (c.ambitoTerritorial.toLowerCase() === 'estatal') {
    metaExtra.push('estatal nacional administracion general del estado');
  }

  const codigo = normalizarTexto(`${c.codigoOficial} ${c.id}`);
  const codigoCompacto = compactarCodigo(`${c.codigoOficial} ${c.id}`);
  const titulo = normalizarTexto(c.titulo);
  const organismo = normalizarTexto(c.organismo);
  const territorio = normalizarTexto(
    [
      c.ambitoTerritorial,
      c.provincia || '',
      c.ccaaCodigo || '',
      c.nivelTerritorial || '',
      c.anio ? String(c.anio) : '',
      c.fechaCierre ? c.fechaCierre.slice(0, 4) : '',
      c.estado || '',
      c.tipoFuente.replace(/_/g, ' '),
    ].join(' ')
  );
  const detalles = normalizarTexto(
    [
      c.orografiaPendiente || '',
      c.motivoElegibilidad,
      ...c.accionesSubvencionables,
      ...(c.citasBasesJustificacion || []),
    ].join(' ')
  );
  const fondo = normalizarTexto(
    [
      c.resumenEjecutivo,
      ...(c.requisitosSolvencia || []),
      ...(c.gastosNoSubvencionables || []),
      c.urlBasesPdf,
      c.fuenteUrl,
      ...metaExtra,
    ].join(' ')
  );

  return {
    codigo,
    codigoCompacto,
    titulo,
    organismo,
    territorio,
    detalles,
    fondo,
  };
}

/**
 * Calcula la puntuación de relevancia de una convocatoria respecto a la consulta.
 * - Si la consulta está vacía devuelve `1` (todas pasan).
 * - Si algún término obligatorio no coincide devuelve `0` (descartada).
 * - Si todos coinciden devuelve un entero positivo mayor cuanto más directa sea la coincidencia.
 */
export function puntajeBusqueda(c: Convocatoria, consulta: string): number {
  const consultaNorm = normalizarTexto(consulta);
  if (!consultaNorm) return 1;

  const tokens = tokenizarConsulta(consulta);
  if (tokens.length === 0) return 1;

  const campos = construirCampos(c);
  const codWords = new Set(campos.codigo.split(' ').filter(Boolean));
  const titWords = new Set(campos.titulo.split(' ').filter(Boolean));
  const orgWords = new Set(campos.organismo.split(' ').filter(Boolean));
  const terWords = new Set(campos.territorio.split(' ').filter(Boolean));
  const detWords = new Set(campos.detalles.split(' ').filter(Boolean));
  const fonWords = new Set(campos.fondo.split(' ').filter(Boolean));

  let score = 0;

  if (
    campos.codigo.includes(consultaNorm) ||
    campos.codigoCompacto.includes(consultaNorm.replace(/\s+/g, ''))
  ) {
    score += 140;
  }
  if (campos.titulo.includes(consultaNorm)) {
    score += 110;
  } else if (campos.organismo.includes(consultaNorm)) {
    score += 80;
  }

  for (const token of tokens) {
    const variantesExactas = variantesToken(token);
    const candidatos = expandirCandidatosToken(token, consultaNorm);

    let hitToken = false;
    let mejorPesoToken = 0;

    for (const cand of candidatos) {
      const esExacto = variantesExactas.includes(cand);
      const factor = esExacto ? 1 : 0.72;

      if (textoCoincideConTermino(campos.codigo, codWords, cand, campos.codigoCompacto)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(65 * factor));
      }
      if (textoCoincideConTermino(campos.titulo, titWords, cand)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(50 * factor));
      }
      if (textoCoincideConTermino(campos.organismo, orgWords, cand)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(40 * factor));
      }
      if (textoCoincideConTermino(campos.territorio, terWords, cand)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(32 * factor));
      }
      if (textoCoincideConTermino(campos.detalles, detWords, cand)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(20 * factor));
      }
      if (textoCoincideConTermino(campos.fondo, fonWords, cand)) {
        hitToken = true;
        mejorPesoToken = Math.max(mejorPesoToken, Math.round(12 * factor));
      }
    }

    if (!hitToken) {
      return 0;
    }
    score += mejorPesoToken;
  }

  if (c.estado === 'ACTIVA') score += 6;
  else if (c.estado === 'PROXIMA') score += 3;
  if (c.elegible) score += 3;

  return Math.max(1, score);
}
