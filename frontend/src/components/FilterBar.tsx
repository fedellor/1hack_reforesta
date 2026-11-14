'use client';

import React from 'react';
import { Search, X } from 'lucide-react';
import { FiltrosState } from '@/types/convocatoria';
import { COMUNIDADES, TODOS } from '@/lib/territorio';

const ATAJOS_BUSQUEDA = [
  { label: 'MITECO', valor: 'miteco' },
  { label: 'Licitaciones públicas', valor: 'licitaciones' },
  { label: 'Comunidad de Madrid', valor: 'madrid' },
  { label: 'Reforestación', valor: 'reforestacion' },
  { label: 'Incendios', valor: 'incendios' },
  { label: 'UE / LIFE', valor: 'ue' },
  { label: '100% financiado', valor: '100%' },
];

interface FilterBarProps {
  filtros: FiltrosState;
  setFiltros: React.Dispatch<React.SetStateAction<FiltrosState>>;
  totalResultados?: number;
  conteoElegibilidad?: { aptas: number; excluidas: number };
  onResetFiltros?: () => void;
}

export function FilterBar({
  filtros,
  setFiltros,
  totalResultados,
  conteoElegibilidad,
  onResetFiltros,
}: FilterBarProps) {
  const chip = (activo: boolean) =>
    `px-5 py-2.5 rounded-full border font-semibold uppercase text-xs tracking-wide transition-colors cursor-pointer ${
      activo
        ? 'bg-brand border-brand text-white'
        : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'
    }`;

  return (
    <div className="bg-zinc-50/80 border-b border-zinc-200 px-4 sm:px-6 lg:px-8 py-4">
      <div className="max-w-[1300px] mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        {/* Input de Búsqueda inteligente */}
        <div className="relative flex-1 min-w-[230px] max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            value={filtros.busqueda}
            onChange={(e) => setFiltros((prev) => ({ ...prev, busqueda: e.target.value }))}
            onKeyDown={(e) => {
              if (e.key === 'Escape' && filtros.busqueda) {
                setFiltros((prev) => ({ ...prev, busqueda: '' }));
              }
            }}
            placeholder="Buscar MITECO, licitaciones, BDNS, Madrid, incendios..."
            className="w-full pl-9 pr-8 py-2 rounded-full border border-zinc-200 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:border-[#2f6f3e] bg-white text-xs shadow-2xs"
          />
          {filtros.busqueda && (
            <button
              type="button"
              onClick={() => setFiltros((prev) => ({ ...prev, busqueda: '' }))}
              aria-label="Limpiar búsqueda"
              title="Limpiar búsqueda (Esc)"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded-full text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors cursor-pointer"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Controles y Chips de Filtro */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Chip de Ámbito */}
          <select
            value={filtros.ambito}
            onChange={(e) =>
              setFiltros((prev) => ({ ...prev, ambito: e.target.value, provincia: '' }))
            }
            className="px-4 py-2 rounded-full border border-zinc-200 text-zinc-700 bg-white font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
          >
            <option value="todos">Todo el territorio</option>
            <option value="Estatal">Ámbito estatal</option>
            {COMUNIDADES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Interruptor único: apagado = aptas, encendido = excluidas */}
          <button
            type="button"
            role="switch"
            aria-checked={filtros.elegibilidad === 'excluidas'}
            onClick={() =>
              setFiltros((prev) => ({ ...prev, elegibilidad: prev.elegibilidad === 'aptas' ? 'excluidas' : 'aptas' }))
            }
            className="inline-flex items-center gap-3 rounded-full border border-zinc-200 bg-white pl-2 pr-4 py-1.5 shadow-2xs cursor-pointer"
          >
            <span className={`relative h-6 w-11 rounded-full transition-colors ${filtros.elegibilidad === 'aptas' ? 'bg-brand' : 'bg-rose-700'}`}>
              <span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200 ${filtros.elegibilidad === 'aptas' ? 'translate-x-0' : 'translate-x-5'}`} />
            </span>
            <span className="font-semibold uppercase text-xs tracking-wide text-zinc-800 min-w-[104px] text-left">
              {filtros.elegibilidad === 'aptas'
                ? `Aptas${conteoElegibilidad ? ` (${conteoElegibilidad.aptas})` : ''}`
                : `Excluidas${conteoElegibilidad ? ` (${conteoElegibilidad.excluidas})` : ''}`}
            </span>
          </button>

          {/* Encaje alto */}
          <button
            type="button"
            onClick={() =>
              setFiltros((prev) => ({ ...prev, minMatching: prev.minMatching >= 80 ? 0 : 80 }))
            }
            className={chip(filtros.minMatching >= 80)}
          >
            Encaje ≥ 80%
          </button>
        </div>
      </div>

      {/* Búsquedas rápidas + contador */}
      <div className="max-w-[1300px] mx-auto mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px]">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-zinc-400 font-medium mr-1">Búsquedas rápidas:</span>
          {ATAJOS_BUSQUEDA.map((atajo) => {
            const activo = filtros.busqueda.trim().toLowerCase() === atajo.valor;
            return (
              <button
                key={atajo.valor}
                type="button"
                onClick={() =>
                  setFiltros((prev) => ({
                    ...prev,
                    busqueda: activo ? '' : atajo.valor,
                  }))
                }
                className={`px-2.5 py-1 rounded-full border transition-colors cursor-pointer ${
                  activo
                    ? 'bg-[#2f6f3e] text-white border-[#2f6f3e] font-semibold'
                    : 'bg-white text-zinc-600 border-zinc-200 hover:border-zinc-300 hover:bg-zinc-100'
                }`}
              >
                {atajo.label}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-3 text-zinc-500">
          {typeof totalResultados === 'number' && (
            <span>
              <strong className="text-zinc-800">{totalResultados}</strong>{' '}
              {totalResultados === 1 ? 'resultado' : 'resultados'}
            </span>
          )}
          {(filtros.busqueda ||
            filtros.ambito !== TODOS ||
            filtros.minMatching > 0) && (
            <button
              type="button"
              onClick={() => {
                if (onResetFiltros) {
                  onResetFiltros();
                } else {
                  setFiltros((prev) => ({
                    ...prev,
                    busqueda: '',
                    ambito: TODOS,
                    provincia: '',
                    minMatching: 0,
                    soloUrgentes: false,
                    ventanaDias: 30,
                  }));
                }
              }}
              className="text-zinc-600 hover:text-zinc-900 underline underline-offset-2 cursor-pointer"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
