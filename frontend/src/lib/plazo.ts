import { Convocatoria } from '@/types/convocatoria';

/** Valor centinela de `diasRestantes` para convocatorias abiertas cuyo plazo aún no está fijado ("según bases"). */
export const SIN_PLAZO = 9999;

const DIA_MS = 86_400_000;

export const plazoSinFijar = (c: Pick<Convocatoria, 'diasRestantes'>) => c.diasRestantes >= SIN_PLAZO;

/** Días para mostrar: número, o «Abierta» si no hay plazo fijado. */
export const textoPlazo = (c: Pick<Convocatoria, 'diasRestantes'>) => (plazoSinFijar(c) ? 'Abierta' : String(c.diasRestantes));

/**
 * Normaliza los plazos al cargar:
 * - Convocatorias abiertas sin fecha fin (`plazos.urgencia = abierta_pendiente_plazo`) → SIN_PLAZO
 *   (antes salían como «0 días» y urgencia crítica).
 * - Con `recalcular`, los días se calculan desde `fechaCierre` y hoy (los datos de ejemplo llevan los días fijos)
 *   y se descartan las ya cerradas.
 */
export function normalizarPlazos(lista: Convocatoria[], recalcular: boolean): Convocatoria[] {
  const hoy = new Date();
  hoy.setHours(12, 0, 0, 0);
  const salida: Convocatoria[] = [];
  for (const c of lista) {
    const pl = c.plazos as { urgencia?: string; fecha_fin_solicitud?: string | null } | undefined;
    // Solo las convocatorias vigentes pueden estar «abiertas sin plazo»; las cerradas del histórico conservan su fecha
    const vigente = c.estado !== 'CERRADA';
    if (vigente && (pl?.urgencia === 'abierta_pendiente_plazo' || (pl && pl.fecha_fin_solicitud == null && c.diasRestantes <= 0))) {
      salida.push({ ...c, diasRestantes: SIN_PLAZO, urgencia: 'holgada' });
      continue;
    }
    if (!recalcular) {
      salida.push(c);
      continue;
    }
    const dias = Math.round((new Date(`${c.fechaCierre}T12:00:00`).getTime() - hoy.getTime()) / DIA_MS);
    if (dias < 0) continue;
    salida.push({ ...c, diasRestantes: dias, urgencia: dias < 7 ? 'critica' : dias < 20 ? 'moderada' : 'holgada' });
  }
  return salida;
}
