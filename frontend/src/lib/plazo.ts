import { Convocatoria } from '@/types/convocatoria';

/** Valor centinela de `diasRestantes` para convocatorias abiertas cuyo plazo aún no está fijado ("según bases"). */
export const SIN_PLAZO = 9999;

export const plazoSinFijar = (c: Pick<Convocatoria, 'diasRestantes'>) => c.diasRestantes >= SIN_PLAZO;

/** Días para mostrar: número, o «Abierta» si no hay plazo fijado. */
export const textoPlazo = (c: Pick<Convocatoria, 'diasRestantes'>) => (plazoSinFijar(c) ? 'Abierta' : String(c.diasRestantes));

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
