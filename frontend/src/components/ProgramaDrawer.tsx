'use client';

import React from 'react';
import { X, ArrowRight, AlertTriangle } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { Programa, PREPARACION_PREVIA_DIAS, nombreMes } from '@/lib/recurrencia';

interface ProgramaDrawerProps {
  programa: Programa | null;
  onClose: () => void;
  /** Abre la ficha completa de una edición anterior */
  onVerEdicion: (c: Convocatoria) => void;
}

const MESES = Array.from({ length: 12 }, (_, i) => i + 1);
const fecha = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`);
const fechaLarga = (d: Date) => d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
const fechaCorta = (iso: string) => fecha(iso).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
const distMes = (a: number, b: number) => Math.min(Math.abs(a - b), 12 - Math.abs(a - b));

const tonoFiabilidad = (f: number) => (f >= 70 ? 'bg-brand' : f >= 50 ? 'bg-brand/60' : 'bg-zinc-300');
const textoFiabilidad = (f: number) => (f >= 70 ? 'Muy fiable' : f >= 50 ? 'Fiable' : 'Poco fiable');

/** Ficha de una previsión: cuándo se espera el programa y por qué, no los datos de una convocatoria concreta. */
export function ProgramaDrawer({ programa: p, onClose, onVerEdicion }: ProgramaDrawerProps) {
  if (!p) return null;
  const hoyAnio = new Date().getFullYear();

  // Una edición por año (la primera publicada) para ver en qué mes sale cada vez
  const porAnio = p.anios.map((y) => {
    const eds = p.ediciones.filter((c) => fecha(c.fechaPublicacion).getFullYear() === y);
    const primera = [...eds].sort((a, b) => a.fechaPublicacion.localeCompare(b.fechaPublicacion))[0];
    return { anio: y, mes: fecha(primera.fechaPublicacion).getMonth() + 1, edicion: primera, total: eds.length };
  });
  const coinciden = porAnio.filter((a) => distMes(a.mes, p.mesApertura) <= 1).length;
  const tema = p.nombre.replace(/\([^)]*\)/g, '').replace(/\b(19|20)\d{2}(\s*[-/]\s*\d{2,4})?\b/g, '').replace(/\s+/g, ' ').trim();

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
              <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">{p.retrasada ? 'Debería haber salido en' : 'Apertura prevista'}</span>
              <p className="mt-1 font-serif text-4xl font-bold text-zinc-900 capitalize">
                {nombreMes(p.proxima.getMonth() + 1)} <span className="text-zinc-400">{p.proxima.getFullYear()}</span>
              </p>
              {p.retrasada ? (
                <p className="mt-2 flex items-start gap-2 text-sm text-amber-800">
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" /> No consta la edición de este año: puede publicarse en cualquier momento o haberse dejado de convocar.
                </p>
              ) : (
                <p className="mt-2 text-sm text-zinc-600">
                  Conviene empezar a preparar la solicitud a partir del <strong className="text-zinc-900">{fechaLarga(p.prepararDesde)}</strong> ({PREPARACION_PREVIA_DIAS} días antes).
                </p>
              )}
            </section>

            {/* Fiabilidad */}
            <section>
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Fiabilidad de la previsión</span>
                <span className="text-sm font-bold text-zinc-900">{p.fiabilidad}% · {textoFiabilidad(p.fiabilidad)}</span>
              </div>
              <div className="mt-2 h-2 bg-zinc-100"><div className={`h-full ${tonoFiabilidad(p.fiabilidad)}`} style={{ width: `${p.fiabilidad}%` }} /></div>
              <p className="mt-2 text-sm text-zinc-600">
                Se ha publicado en <strong className="text-zinc-900">{p.anios.length} años distintos</strong> y en <strong className="text-zinc-900">{coinciden} de {porAnio.length}</strong> cerca de {nombreMes(p.mesApertura)}.
                {p.anios.length < 3 && ' Con tan pocas ediciones, tómalo como un indicio.'}
                {hoyAnio - p.anios[p.anios.length - 1] >= 2 && (
                  <> <strong className="text-amber-800">Última edición detectada: {p.anios[p.anios.length - 1]}</strong>; puede haberse dejado de convocar.</>
                )}
              </p>
            </section>

            {/* Cuándo salió cada año */}
            <section>
              <span className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Cuándo salió cada año</span>
              <div className="mt-3 border border-zinc-200">
                <div className="grid grid-cols-[48px_repeat(12,1fr)] border-b border-zinc-200 bg-zinc-50 text-[10px] uppercase text-zinc-500">
                  <span />
                  {MESES.map((m) => <span key={m} className={`py-1 text-center ${m === p.mesApertura ? 'font-bold text-zinc-900' : ''}`}>{nombreMes(m).slice(0, 1)}</span>)}
                </div>
                {[...porAnio].reverse().map((a) => (
                  <button key={a.anio} onClick={() => onVerEdicion(a.edicion)} className="w-full grid grid-cols-[48px_repeat(12,1fr)] items-center border-b last:border-b-0 border-zinc-100 hover:bg-zinc-50" title={`${fechaCorta(a.edicion.fechaPublicacion)} · ver la edición de ${a.anio}`}>
                    <span className="py-1.5 pl-2 text-xs font-semibold text-zinc-700 text-left">{a.anio}</span>
                    {MESES.map((m) => (
                      <span key={m} className={`flex justify-center py-1.5 ${m === p.mesApertura ? 'bg-brand/10' : ''}`}>
                        {m === a.mes && <span className="h-3 w-3 rounded-full bg-zinc-900" />}
                      </span>
                    ))}
                  </button>
                ))}
              </div>
              <p className="mt-1.5 text-[11px] text-zinc-400">La columna sombreada es el mes habitual. Pulsa un año para ver esa edición.</p>
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
