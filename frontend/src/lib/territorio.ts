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

/** Convocatorias aplicables a una provincia: las propias de la provincia + las de toda su comunidad. */
export function aplicaAProvincia(c: Convocatoria, comunidad: string, provincia: string): boolean {
  if (!perteneceAComunidad(c.ambitoTerritorial, comunidad)) return false;
  return !c.provincia || c.provincia === provincia;
}

export function filtrarPorTerritorio(convocatorias: Convocatoria[], territorio: string, provincia = ''): Convocatoria[] {
  if (territorio === TODOS) return convocatorias;
  if (territorio === ESTATAL) return convocatorias.filter((c) => c.ambitoTerritorial === ESTATAL);
  if (provincia) return convocatorias.filter((c) => aplicaAProvincia(c, territorio, provincia));
  return convocatorias.filter((c) => perteneceAComunidad(c.ambitoTerritorial, territorio));
}

export const PROVINCIAS_POR_COMUNIDAD: Record<string, string[]> = {
  'Andalucía': ['Almería', 'Cádiz', 'Córdoba', 'Granada', 'Huelva', 'Jaén', 'Málaga', 'Sevilla'],
  'Aragón': ['Huesca', 'Teruel', 'Zaragoza'],
  'Canarias': ['Las Palmas', 'Santa Cruz de Tenerife'],
  'Castilla y León': ['Ávila', 'Burgos', 'León', 'Palencia', 'Salamanca', 'Segovia', 'Soria', 'Valladolid', 'Zamora'],
  'Castilla-La Mancha': ['Albacete', 'Ciudad Real', 'Cuenca', 'Guadalajara', 'Toledo'],
  'Cataluña': ['Barcelona', 'Girona', 'Lleida', 'Tarragona'],
  'Comunitat Valenciana': ['Alicante', 'Castellón', 'Valencia'],
  'Extremadura': ['Badajoz', 'Cáceres'],
  'Galicia': ['A Coruña', 'Lugo', 'Ourense', 'Pontevedra'],
  'País Vasco': ['Álava', 'Bizkaia', 'Gipuzkoa'],
};

export const formatoEuros = (n: number) =>
  new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);

export const COMUNIDADES = [
  'Andalucía', 'Aragón', 'Principado de Asturias', 'Illes Balears', 'Canarias', 'Cantabria',
  'Castilla-La Mancha', 'Castilla y León', 'Cataluña', 'Comunitat Valenciana', 'Extremadura',
  'Galicia', 'La Rioja', 'Comunidad de Madrid', 'Región de Murcia', 'Navarra', 'País Vasco',
];
