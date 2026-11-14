/**
 * «Novedades desde tu última visita». Sin servidor ni correo: cada navegador recuerda qué convocatorias ya había visto.
 * Sirve igual aunque las convocatorias salgan cada semana o cada mes, y no depende de que haya un canal de avisos.
 */
const CLAVE = 'radar-reforesta:vistas';

interface Vistas {
  ids: string[];
  desde: string;
}

export function leerVistas(): Vistas | null {
  try {
    const raw = window.localStorage.getItem(CLAVE);
    return raw ? (JSON.parse(raw) as Vistas) : null;
  } catch {
    return null;
  }
}

export function guardarVistas(ids: string[]): void {
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify({ ids, desde: new Date().toISOString() } satisfies Vistas));
  } catch {
    // almacenamiento no disponible: simplemente no hay avisos
  }
}
