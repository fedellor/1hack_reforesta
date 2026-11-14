'use client';

import React from 'react';
import { X, ArrowRight, AlertTriangle } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { temaDePrograma } from '@/lib/texto';
import { ETIQUETA_TRAMO, Evaluacion, PREPARACION_PREVIA_DIAS, Programa, Tramo, mesEnArco, nombreMes, textoVentana } from '@/lib/recurrencia';

interface ProgramaDrawerProps {
  programa: Programa | null;
  /** Acierto medido de la previsión con el histórico cargado */
  evaluacion: Evaluacion | null;
  onClose: () => void;
  /** Abre la ficha completa de una edición anterior */
  onVerEdicion: (c: Convocatoria) => void;
}

const MESES = Array.from({ length: 12 }, (_, i) => i + 1);
const fecha = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`);
const fechaLarga = (d: Date) => d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
const fechaCorta = (iso: string) => fecha(iso).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
const CHIP: Record<Tramo, string> = { alta: 'bg-brand text-white', media: 'bg-emerald-100 text-emerald-900', baja: 'bg-zinc-200 text-zinc-700' };

/** Ficha de una previsión: cuándo se espera el programa y por qué, no los datos de una convocatoria concreta. */
export function ProgramaDrawer({ programa: p, evaluacion, onClose, onVerEdicion }: ProgramaDrawerProps) {
  if (!p) return null;
  const hoyAnio = new Date().getFullYear();

  // Una edición por año (la primera publicada) para ver en qué mes sale cada vez
  const porAnio = p.anios.map((y) => {
    const eds = p.ediciones.filter((c) => fecha(c.fechaPublicacion).getFullYear() === y);
    const primera = [...eds].sort((a, b) => a.fechaPublicacion.localeCompare(b.fechaPublicacion))[0];
    return { anio: y, mes: fecha(primera.fechaPublicacion).getMonth() + 1, edicion: primera };
  });
  const ultimo = p.anios[p.anios.length - 1];
  const tema = temaDePrograma(p.nombre);
  const medido = evaluacion && evaluacion.porTramo[p.tramo].n >= 5 ? evaluacion.porTramo[p.tramo] : null;

  const motivo =
    p.tramo === 'alta'
      ? `Salió el año anterior y se ha publicado en ${p.anios.length} años distintos.`
      : p.tramo === 'media'
        ? `Salió el año anterior, pero solo se ha publicado en ${p.anios.length} años: es pronto para fiarse de que sea anual.`
        : `Lleva ${Math.max(2, hoyAnio - ultimo)} años sin salir (última edición detectada: ${ultimo}). Puede haberse dejado de convocar o no haberse capturado.`;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div onClick={onClose} className="absolute inset-0 bg-zinc-900/20 backdrop-blur-2xs" />
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white shadow-xl flex flex-col border-l border-zinc-200">
          {/* Cabecera */}
          <div className="px-6 py-4 border-b border-zinc-200 flex items-start justify-between gap-4">
            <div className="space-y-2 min-w-0">
              <span className="inline-block rounded-full bg-amber-100 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-amber-800">Previsión · aún no confirmada</span>
              <h2 className="text-base font-semibold text-zinc-900 leading-snug">{tema}</h2>
              <p className="text-xs text-zinc-500">{p.organismo.split(' - ').slice(0, 2).join(' · ')} · {p.ambito}</p>
            </div>
            <button onClick={onClose} className="p-1.5 text-zinc-400 hover:text-zinc-900 shrink-0" aria-label="Cerrar">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
            {/* Cuándo */}
            <section>
              <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">
                {p.enVentana ? 'Estamos en su ventana habitual' : p.retrasada ? 'Su ventana habitual ya pasó' : 'Ventana de apertura prevista'}
              </span>
              <p className="mt-1 font-serif text-3xl font-bold text-zinc-900 capitalize">
                {textoVentana(p)} <span className="text-zinc-400">{p.proxima.getFullYear()}</span>
              </p>
              {p.enVentana ? (
                <p className="mt-2 text-sm text-zinc-600">No consta la edición de este año: <strong className="text-zinc-900">puede publicarse en cualquier momento</strong> hasta finales de {nombreMes(p.mesHasta)}.</p>
              ) : p.retrasada ? (
                <p className="mt-2 flex items-start gap-2 text-sm text-amber-800">
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" /> No consta la edición de este año: puede salir fuera de fecha o haberse dejado de convocar.
                </p>
              ) : (
                <p className="mt-2 text-sm text-zinc-600">
                  Conviene empezar a preparar la solicitud a partir del <strong className="text-zinc-900">{fechaLarga(p.prepararDesde)}</strong> ({PREPARACION_PREVIA_DIAS} días antes de que empiece la ventana).
                </p>
              )}
            </section>

            {/* Probabilidad */}
            <section>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Probabilidad de que salga</span>
                <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide ${CHIP[p.tramo]}`}>{ETIQUETA_TRAMO[p.tramo]}</span>
              </div>
              <p className="mt-2 text-sm text-zinc-600">{motivo}</p>
              {medido ? (
                <p className="mt-2 text-sm text-zinc-600">
                  En el histórico, las previsiones de este nivel se cumplieron el <strong className="text-zinc-900">{Math.round((100 * medido.enAnio) / medido.n)}%</strong> de las veces ({medido.enAnio} de {medido.n}).
                </p>
              ) : (
                <p className="mt-2 text-xs text-zinc-400">Aún no hay casos suficientes en el histórico para medir el acierto de este nivel.</p>
              )}
            </section>

            {/* Cuándo salió cada año */}
            <section>
              <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Cuándo salió cada año</span>
              <div className="mt-3 border border-zinc-200">
                <div className="grid grid-cols-[48px_repeat(12,1fr)] border-b border-zinc-200 bg-zinc-50 text-[10px] uppercase text-zinc-500">
                  <span />
                  {MESES.map((m) => <span key={m} className={`py-1 text-center ${mesEnArco(m, p.mesDesde, p.mesHasta) ? 'font-bold text-zinc-900' : ''}`}>{nombreMes(m).slice(0, 1)}</span>)}
                </div>
                {[...porAnio].reverse().map((a) => (
                  <button key={a.anio} onClick={() => onVerEdicion(a.edicion)} className="w-full grid grid-cols-[48px_repeat(12,1fr)] items-center border-b last:border-b-0 border-zinc-100 hover:bg-zinc-50" title={`${fechaCorta(a.edicion.fechaPublicacion)} · ver la edición de ${a.anio}`}>
                    <span className="py-1.5 pl-2 text-xs font-semibold text-zinc-700 text-left">{a.anio}</span>
                    {MESES.map((m) => (
                      <span key={m} className={`flex justify-center py-1.5 ${mesEnArco(m, p.mesDesde, p.mesHasta) ? 'bg-brand/10' : ''}`}>
                        {m === a.mes && <span className="h-3 w-3 rounded-full bg-zinc-900" />}
                      </span>
                    ))}
                  </button>
                ))}
              </div>
              <p className="mt-1.5 text-[11px] text-zinc-400">Las columnas sombreadas son la ventana habitual. Pulsa un año para ver esa edición.</p>
            </section>

            {/* Orden de magnitud */}
            {(p.ventanaDias !== null || p.cuantiaMedia > 0) && (
              <section>
                <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Para hacerse una idea</span>
                <div className="mt-2 grid grid-cols-2 gap-px bg-zinc-200 border border-zinc-200 text-sm">
                  {p.ventanaDias !== null && (
                    <div className="bg-white p-3"><span className="block text-lg font-bold text-zinc-900">≈ {p.ventanaDias} días</span><span className="text-xs text-zinc-500">de plazo en ediciones anteriores</span></div>
                  )}
                  {p.cuantiaMedia > 0 && (
                    <div className="bg-white p-3"><span className="block text-lg font-bold text-zinc-900">≈ {formatoEuros(p.cuantiaMedia)}</span><span className="text-xs text-zinc-500">por proyecto, de media</span></div>
                  )}
                </div>
              </section>
            )}
          </div>

          {/* Pie */}
          <div className="px-6 py-4 border-t border-zinc-200 bg-zinc-50 space-y-3">
            <p className="text-[11px] text-zinc-500 leading-relaxed">Estimación a partir de ediciones anteriores. La convocatoria puede cambiar de fecha, de condiciones o no repetirse.</p>
            <button onClick={() => onVerEdicion(p.ediciones[0])} className="inline-flex items-center gap-2 rounded-full bg-zinc-900 px-5 py-2.5 text-xs font-semibold uppercase tracking-wide text-white hover:bg-zinc-700 transition-colors">
              Ver la última edición ({fecha(p.ediciones[0].fechaPublicacion).getFullYear()}) <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
