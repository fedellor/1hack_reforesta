import { Convocatoria } from '@/types/convocatoria';

/** Valor centinela de `diasRestantes` para convocatorias abiertas cuyo plazo aún no está fijado ("según bases"). */
export const SIN_PLAZO = 9999;

export const plazoSinFijar = (c: Pick<Convocatoria, 'diasRestantes'>) => c.diasRestantes >= SIN_PLAZO;

/** Días para mostrar: número, o «Abierta» si no hay plazo fijado. */
export const textoPlazo = (c: Pick<Convocatoria, 'diasRestantes'>) => (plazoSinFijar(c) ? 'Abierta' : String(c.diasRestantes));

const DIA_MS = 86_400_000;

/** Convocatoria definida (hay bases o extracto) pero cuyo plazo de solicitud aún no ha empezado. */
export const esProxima = (c: Pick<Convocatoria, 'estado'>) => c.estado === 'PROXIMA';

/** Fecha (ISO) en la que se abre el plazo de solicitud, si el backend la informa. */
export const aperturaISO = (c: Pick<Convocatoria, 'plazos'>): string | null => {
  const f = (c.plazos as { fecha_inicio_solicitud?: string | null } | undefined)?.fecha_inicio_solicitud;
  return f ? f.slice(0, 10) : null;
};

/** Días que faltan para que se abra el plazo (0 si ya está abierto o no consta la fecha). */
export function diasHastaApertura(c: Pick<Convocatoria, 'estado' | 'plazos'>): number {
  const f = aperturaISO(c);
  if (!f || !esProxima(c)) return 0;
  const hoy = new Date();
  hoy.setHours(12, 0, 0, 0);
  return Math.max(0, Math.round((new Date(`${f}T12:00:00`).getTime() - hoy.getTime()) / DIA_MS));
}

/**
 * Normaliza los plazos al cargar: las convocatorias vigentes abiertas sin fecha fin
 * (`plazos.urgencia = abierta_pendiente_plazo`) pasan a SIN_PLAZO. Antes salían como «0 días» y urgencia crítica.
 * Las cerradas del histórico conservan su fecha.
 */
export function normalizarPlazos(lista: Convocatoria[]): Convocatoria[] {
  return lista.map((c) => {
    const pl = c.plazos as { urgencia?: string; fecha_fin_solicitud?: string | null } | undefined;
    const vigente = c.estado !== 'CERRADA';
    const sinFecha = pl?.urgencia === 'abierta_pendiente_plazo' || (pl && pl.fecha_fin_solicitud == null && c.diasRestantes <= 0);
    return vigente && sinFecha ? { ...c, diasRestantes: SIN_PLAZO, urgencia: 'holgada' } : c;
  });
}
