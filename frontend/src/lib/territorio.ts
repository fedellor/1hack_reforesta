import { Convocatoria } from '@/types/convocatoria';

export const ESTATAL = 'Estatal';
export const TODOS = 'todos';

const normalizar = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

/** ¿Una convocatoria de ámbito `ambito` pertenece a la comunidad `comunidad`? (Estatal no cuenta) */
export function perteneceAComunidad(ambito: string, comunidad: string): boolean {
  const a = normalizar(ambito);
  const c = normalizar(comunidad);
  if (a === normalizar(ESTATAL)) return false;
  return c.includes(a) || a.includes(c);
}

export function filtrarPorTerritorio(convocatorias: Convocatoria[], territorio: string): Convocatoria[] {
  if (territorio === TODOS) return convocatorias;
  if (territorio === ESTATAL) return convocatorias.filter((c) => c.ambitoTerritorial === ESTATAL);
  return convocatorias.filter((c) => perteneceAComunidad(c.ambitoTerritorial, territorio));
}

export const formatoEuros = (n: number) =>
  new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);

export const COMUNIDADES = [
  'Andalucía', 'Aragón', 'Principado de Asturias', 'Illes Balears', 'Canarias', 'Cantabria',
  'Castilla-La Mancha', 'Castilla y León', 'Cataluña', 'Comunitat Valenciana', 'Extremadura',
  'Galicia', 'La Rioja', 'Comunidad de Madrid', 'Región de Murcia', 'Navarra', 'País Vasco',
];
