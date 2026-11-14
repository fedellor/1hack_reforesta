'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Convocatoria } from '@/types/convocatoria';
import { ArrowRight } from 'lucide-react';
import { COMUNIDADES, ESTATAL, TODOS, filtrarPorTerritorio, formatoEuros } from '@/lib/territorio';

// Leaflet necesita window: carga solo en cliente
const LeafletMap = dynamic(() => import('@/components/LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[520px] border border-zinc-200 bg-zinc-50 flex items-center justify-center text-sm text-zinc-400">
      Cargando mapa…
    </div>
  ),
});

interface MapViewProps {
  /** Lista SIN filtrar por territorio: colorea el mapa */
  convocatorias: Convocatoria[];
  /** Lista ya filtrada (incluido el territorio) */
  filtradas: Convocatoria[];
  territorio: string;
  onCambiarTerritorio: (territorio: string) => void;
  onSeleccionar: (convocatoria: Convocatoria) => void;
  onVerConvocatorias: () => void;
}

/** Sección «¿Dónde?»: reparto territorial de los fondos. No lista convocatorias: las resume. */
export function MapView({ convocatorias, filtradas, territorio, onCambiarTerritorio, onSeleccionar, onVerConvocatorias }: MapViewProps) {
  const total = filtradas.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const urgentes = filtradas.filter((c) => c.diasRestantes <= 15).length;
  const proximo = filtradas.length ? Math.min(...filtradas.map((c) => c.diasRestantes)) : null;
  const top = [...filtradas].sort((a, b) => b.matchingGlobal - a.matchingGlobal).slice(0, 3);

  // Ranking de fondos por territorio (solo con todo el territorio seleccionado)
  const ranking = [ESTATAL, ...COMUNIDADES]
    .map((t) => ({ t, euros: filtrarPorTerritorio(convocatorias, t).reduce((a, c) => a + c.cuantiaMaximaProyecto, 0) }))
    .filter((r) => r.euros > 0)
    .sort((a, b) => b.euros - a.euros)
    .slice(0, 6);
  const maxEuros = ranking[0]?.euros ?? 1;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <div className="lg:col-span-7">
        <LeafletMap convocatorias={convocatorias} territorio={territorio} onCambiarTerritorio={onCambiarTerritorio} />
        <p className="mt-2 text-xs text-zinc-400">Pulsa una comunidad para ver su resumen. Las convocatorias estatales se cuentan aparte.</p>
      </div>

      <aside className="lg:col-span-5 space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-brand">Resumen territorial</p>
          <h2 className="mt-1 text-2xl font-bold text-zinc-900">{territorio === TODOS ? 'España' : territorio === ESTATAL ? 'Ámbito estatal' : territorio}</h2>
        </div>

        <dl className="grid grid-cols-3 gap-4 border-y border-zinc-200 py-5">
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">Fondos</dt>
            <dd className="mt-1 font-serif text-2xl font-bold text-zinc-900">{formatoEuros(total)}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">Convocatorias</dt>
            <dd className="mt-1 font-serif text-2xl font-bold text-zinc-900">{filtradas.length}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">Próximo cierre</dt>
            <dd className="mt-1 font-serif text-2xl font-bold text-zinc-900">{proximo === null ? '—' : `${proximo} d`}</dd>
            {urgentes > 0 && <span className="text-xs text-amber-700">{urgentes} en menos de 15 d</span>}
          </div>
        </dl>

        {territorio === TODOS ? (
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">Dónde está el dinero</h3>
            <ul className="mt-3 space-y-2.5">
              {ranking.map((r) => (
                <li key={r.t}>
                  <button onClick={() => onCambiarTerritorio(r.t)} className="w-full text-left group">
                    <span className="flex justify-between text-sm text-zinc-700 group-hover:text-zinc-900">
                      <span>{r.t === ESTATAL ? 'Estatal' : r.t}</span>
                      <span className="font-semibold">{formatoEuros(r.euros)}</span>
                    </span>
                    <span className="mt-1 block h-1.5 bg-zinc-100">
                      <span className="block h-full bg-brand" style={{ width: `${(r.euros / maxEuros) * 100}%` }} />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">Mejor encaje</h3>
            <ul className="mt-3 divide-y divide-zinc-200 border-y border-zinc-200">
              {top.map((c) => (
                <li key={c.id}>
                  <button onClick={() => onSeleccionar(c)} className="w-full py-3 flex items-start justify-between gap-4 text-left hover:text-emerald-800">
                    <span className="text-sm leading-snug line-clamp-2">{c.titulo}</span>
                    <span className="text-sm font-bold text-brand shrink-0">{c.matchingGlobal}%</span>
                  </button>
                </li>
              ))}
              {top.length === 0 && <li className="py-4 text-sm text-zinc-400">Sin convocatorias con los filtros actuales.</li>}
            </ul>
          </div>
        )}

        <button
          onClick={onVerConvocatorias}
          className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-xs font-semibold uppercase tracking-wide text-white hover:bg-emerald-700 transition-colors"
        >
          Ver convocatorias {territorio !== TODOS && 'de esta zona'} <ArrowRight className="h-4 w-4" />
        </button>
      </aside>
    </div>
  );
}
