'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Convocatoria } from '@/types/convocatoria';
import { ArrowRight } from 'lucide-react';
import { COMUNIDADES, ESTATAL, PROVINCIAS_POR_COMUNIDAD, TODOS, filtrarPorTerritorio, formatoEuros, perteneceAComunidad } from '@/lib/territorio';

// Leaflet necesita window: carga solo en cliente
const LeafletMap = dynamic(() => import('@/components/LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[520px] border border-zinc-200 bg-zinc-50 flex items-center justify-center text-sm text-zinc-400">
      Cargando mapa…
    </div>
  ),
});

function Lista({ items, vacio, onSeleccionar }: { items: Convocatoria[]; vacio: string; onSeleccionar: (c: Convocatoria) => void }) {
  return (
    <ul className="mt-3 divide-y divide-zinc-200 border-y border-zinc-200">
      {items.slice(0, 3).map((c) => (
        <li key={c.id}>
          <button onClick={() => onSeleccionar(c)} className="w-full py-3 flex items-start justify-between gap-4 text-left hover:text-emerald-800">
            <span className="text-sm leading-snug line-clamp-2">{c.titulo}</span>
            <span className="text-right shrink-0">
              <span className="block text-sm font-bold text-brand">{c.matchingGlobal}%</span>
              <span className="block text-xs text-zinc-500">{formatoEuros(c.cuantiaMaximaProyecto)}</span>
            </span>
          </button>
        </li>
      ))}
      {items.length === 0 && <li className="py-4 text-sm text-zinc-400">{vacio}</li>}
    </ul>
  );
}

interface MapViewProps {
  /** Lista SIN filtrar por territorio: colorea el mapa */
  convocatorias: Convocatoria[];
  /** Lista ya filtrada (incluido el territorio) */
  filtradas: Convocatoria[];
  territorio: string;
  provincia: string;
  onCambiarTerritorio: (territorio: string) => void;
  onCambiarProvincia: (provincia: string) => void;
  onSeleccionar: (convocatoria: Convocatoria) => void;
  onVerConvocatorias: () => void;
  busqueda?: string;
  onLimpiarBusqueda?: () => void;
}

/** Sección «¿Dónde?»: reparto territorial de los fondos y acceso rápido estatal / búsqueda. */
export function MapView({
  convocatorias,
  filtradas,
  territorio,
  provincia,
  onCambiarTerritorio,
  onCambiarProvincia,
  onSeleccionar,
  onVerConvocatorias,
  busqueda = '',
  onLimpiarBusqueda,
}: MapViewProps) {
  const hayBusqueda = Boolean(busqueda && busqueda.trim().length > 0);
  const total = filtradas.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const urgentes = filtradas.filter((c) => c.diasRestantes <= 15).length;
  const proximo = filtradas.length ? Math.min(...filtradas.map((c) => c.diasRestantes)) : null;
  const top = (hayBusqueda ? filtradas : [...filtradas].sort((a, b) => b.matchingGlobal - a.matchingGlobal)).slice(0, 6);
  const estatales = filtrarPorTerritorio(convocatorias, ESTATAL).sort((a, b) => b.matchingGlobal - a.matchingGlobal);

  // Ranking de fondos por territorio (solo con todo el territorio seleccionado)
  const ranking = [ESTATAL, ...COMUNIDADES]
    .map((t) => ({ t, euros: filtrarPorTerritorio(convocatorias, t).reduce((a, c) => a + c.cuantiaMaximaProyecto, 0) }))
    .filter((r) => r.euros > 0)
    .sort((a, b) => b.euros - a.euros)
    .slice(0, 6);
  const maxEuros = ranking[0]?.euros ?? 1;

  // Detalle de una comunidad: lo que aplica a toda ella vs. lo propio de cada provincia
  const enComunidad = COMUNIDADES.includes(territorio);
  const deComunidad = enComunidad ? convocatorias.filter((c) => perteneceAComunidad(c.ambitoTerritorial, territorio)) : [];
  const regionales = deComunidad.filter((c) => !c.provincia).sort((a, b) => b.matchingGlobal - a.matchingGlobal);
  const provinciasDe = PROVINCIAS_POR_COMUNIDAD[territorio] ?? [];
  const porProvincia = provinciasDe
    .map((p) => {
      const propias = deComunidad.filter((c) => c.provincia === p);
      return { p, n: propias.length, euros: propias.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0) };
    })
    .filter((r) => r.n > 0)
    .sort((a, b) => b.euros - a.euros);
  const maxProv = porProvincia[0]?.euros ?? 1;
  const propiasDeProvincia = provincia ? deComunidad.filter((c) => c.provincia === provincia).sort((a, b) => b.matchingGlobal - a.matchingGlobal) : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <div className="lg:col-span-7">
        <LeafletMap convocatorias={convocatorias} territorio={territorio} provincia={provincia} onCambiarTerritorio={onCambiarTerritorio} onCambiarProvincia={onCambiarProvincia} />
        <p className="mt-2 text-xs text-zinc-400">Pulsa una comunidad para ampliarla y ver sus provincias. Las convocatorias estatales se cuentan aparte.</p>
      </div>

      <aside className="lg:col-span-5 space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-brand">Resumen territorial</p>
          <h2 className="mt-1 text-2xl font-bold text-zinc-900">{territorio === TODOS ? 'España' : territorio === ESTATAL ? 'Ámbito estatal' : provincia ? `${territorio} › ${provincia}` : territorio}</h2>
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

        {territorio === TODOS && (
          <>
            {hayBusqueda && (
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">
                    Resultados de búsqueda ({filtradas.length})
                  </h3>
                  {onLimpiarBusqueda && (
                    <button
                      type="button"
                      onClick={onLimpiarBusqueda}
                      className="text-xs text-zinc-500 hover:text-zinc-900 underline underline-offset-2"
                    >
                      Limpiar búsqueda
                    </button>
                  )}
                </div>
                <Lista
                  onSeleccionar={onSeleccionar}
                  items={filtradas.slice(0, 8)}
                  vacio="Sin convocatorias con esos términos de búsqueda."
                />
              </div>
            )}

            <div>
              <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">Dónde está el dinero</h3>
              <ul className="mt-3 space-y-2.5">
                {ranking.map((r) => (
                  <li key={r.t}>
                    <button onClick={() => onCambiarTerritorio(r.t)} className="w-full text-left group">
                      <span className="flex justify-between text-sm text-zinc-700 group-hover:text-zinc-900">
                        <span>{r.t === ESTATAL ? 'Estatal (MITECO, Ministerios y BOE)' : r.t}</span>
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

            {!hayBusqueda && estatales.length > 0 && (
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">
                    Ámbito estatal ({estatales.length})
                  </h3>
                  <button
                    type="button"
                    onClick={() => onCambiarTerritorio(ESTATAL)}
                    className="text-xs font-medium text-[#2f6f3e] hover:underline"
                  >
                    Filtrar estatales →
                  </button>
                </div>
                <p className="text-xs text-zinc-500">Aplican en toda España (no se pintan en una sola comunidad)</p>
                <Lista
                  onSeleccionar={onSeleccionar}
                  items={estatales.slice(0, 4)}
                  vacio="Sin convocatorias estatales."
                />
              </div>
            )}
          </>
        )}

        {territorio === ESTATAL && (
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">
              {hayBusqueda ? `Estatales encontradas (${top.length})` : 'Mejor encaje estatal'}
            </h3>
            <Lista onSeleccionar={onSeleccionar} items={top} vacio="Sin convocatorias con los filtros actuales." />
          </div>
        )}

        {enComunidad && (
          <>
            {hayBusqueda && filtradas.length === 0 && convocatorias.length > 0 && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 text-xs text-emerald-950">
                <p>
                  No hay coincidencias autonómicas en <strong>{territorio}</strong>, pero sí{' '}
                  <strong>{convocatorias.length}</strong> en el resto de España (incluido ámbito estatal).
                </p>
                <button
                  type="button"
                  onClick={() => onCambiarTerritorio(TODOS)}
                  className="mt-2 font-semibold text-[#2f6f3e] underline underline-offset-2"
                >
                  Ver resultados en toda España →
                </button>
              </div>
            )}
            {provincia && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">Propias de {provincia}</h3>
                <Lista onSeleccionar={onSeleccionar} items={propiasDeProvincia} vacio={`${provincia} no tiene convocatorias propias (diputación) ahora.`} />
              </div>
            )}
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">En toda {territorio}</h3>
              <p className="text-xs text-zinc-500">Aplican a todas las provincias</p>
              <Lista onSeleccionar={onSeleccionar} items={regionales} vacio="No hay convocatorias autonómicas con los filtros actuales." />
            </div>
            {!provincia && porProvincia.length > 0 && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wide text-zinc-900">Por provincia</h3>
                <p className="text-xs text-zinc-500">Solo las propias de cada provincia · pulsa una para verlas</p>
                <ul className="mt-3 space-y-2.5">
                  {porProvincia.map((r) => (
                    <li key={r.p}>
                      <button onClick={() => onCambiarProvincia(r.p)} className="w-full text-left group">
                        <span className="flex justify-between text-sm text-zinc-700 group-hover:text-zinc-900">
                          <span>{r.p} <span className="text-zinc-400">· {r.n}</span></span>
                          <span className="font-semibold">{formatoEuros(r.euros)}</span>
                        </span>
                        <span className="mt-1 block h-1.5 bg-zinc-100">
                          <span className="block h-full bg-brand" style={{ width: `${(r.euros / maxProv) * 100}%` }} />
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
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
