'use client';

import React from 'react';
import { Search, X } from 'lucide-react';
import { FiltrosState } from '@/types/convocatoria';
import { COMUNIDADES, TODOS } from '@/lib/territorio';

const ATAJOS_BUSQUEDA = [
  { label: 'MITECO', valor: 'miteco' },
  { label: 'Comunidad de Madrid', valor: 'madrid' },
  { label: 'Reforestación', valor: 'reforestacion' },
  { label: 'Incendios', valor: 'incendios' },
  { label: 'PEPAC / FEADER', valor: 'pepac' },
  { label: 'Licitaciones PLACSP', valor: 'placsp' },
  { label: '100% financiado', valor: '100%' },
];

interface FilterBarProps {
  filtros: FiltrosState;
  setFiltros: React.Dispatch<React.SetStateAction<FiltrosState>>;
  ordenarPor: 'matching' | 'cuantia' | 'urgencia';
  setOrdenarPor: (orden: 'matching' | 'cuantia' | 'urgencia') => void;
  /** Qué controles tienen sentido en cada sección */
  modo: 'mapa' | 'lista' | 'historico' | 'calendario';
  totalResultados?: number;
  onResetFiltros?: () => void;
}

export function FilterBar({
  filtros,
  setFiltros,
  ordenarPor,
  setOrdenarPor,
  modo,
  totalResultados,
  onResetFiltros,
}: FilterBarProps) {
  const chip = (activo: boolean) =>
    `px-5 py-2.5 rounded-full border font-semibold uppercase text-xs tracking-wide transition-colors ${
      activo ? 'bg-brand border-brand text-white' : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'
    }`;
  return (
    <div className="bg-zinc-50/80 border-b border-zinc-200 px-4 sm:px-6 lg:px-8 py-4">
      <div className="max-w-[1300px] mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        
        {/* Input de Búsqueda */}
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
            placeholder="Buscar MITECO, BDNS 923290, Madrid, pepac, incendios..."
            className="w-full pl-9 pr-8 py-2 rounded-full border border-zinc-200 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:border-[#2f6f3e] bg-white text-xs shadow-2xs"
          />
          {filtros.busqueda && (
            <button
              type="button"
              onClick={() => setFiltros((prev) => ({ ...prev, busqueda: '' }))}
              aria-label="Limpiar búsqueda"
              title="Limpiar búsqueda (Esc)"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 rounded-full text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
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
            onChange={(e) => setFiltros((prev) => ({ ...prev, ambito: e.target.value, provincia: '' }))}
            className="px-4 py-2 rounded-full border border-zinc-200 text-zinc-700 bg-white font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
          >
            <option value="todos">Todo el territorio</option>
            <option value="Estatal">Ámbito estatal</option>
            {COMUNIDADES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* Chip de Año (en Histórico) */}
          {modo === 'historico' && (
            <select
              value={filtros.anio}
              onChange={(e) => setFiltros((prev) => ({ ...prev, anio: Number(e.target.value) }))}
              className="px-4 py-2 rounded-full border border-zinc-200 text-zinc-700 bg-white font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
            >
              <option value={0}>Todos los años (2020–2026)</option>
              {[2026, 2025, 2024, 2023, 2022, 2021, 2020].map((anio) => (
                <option key={anio} value={anio}>
                  Año {anio}
                </option>
              ))}
            </select>
          )}

          {/* Toggle Solo Elegibles */}
          <button
            type="button"
            onClick={() => setFiltros((prev) => ({ ...prev, soloElegibles: !prev.soloElegibles }))}
            className={`px-5 py-2.5 rounded-full border font-semibold uppercase text-xs tracking-wide transition-colors shadow-2xs ${
              filtros.soloElegibles
                ? 'bg-brand border-brand text-white'
                : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'
            }`}
          >
            {filtros.soloElegibles ? 'Solo aptas ONG' : 'Todas (incl. licitaciones)'}
          </button>

          {/* Ventana de 30 días */}
          {modo !== 'calendario' && modo !== 'historico' && (
            <button
              type="button"
              onClick={() => setFiltros((prev) => ({ ...prev, ventanaDias: prev.ventanaDias === 30 ? 0 : 30 }))}
              className={chip(filtros.ventanaDias === 30)}
            >
              Cierre ≤ 30 días
            </button>
          )}

          {/* Encaje alto */}
          <button
            type="button"
            onClick={() => setFiltros((prev) => ({ ...prev, minMatching: prev.minMatching >= 80 ? 0 : 80 }))}
            className={chip(filtros.minMatching >= 80)}
          >
            Encaje ≥ 80%
          </button>

          {/* Cuantía mínima */}
          <select
            value={filtros.minCuantia}
            onChange={(e) => setFiltros((prev) => ({ ...prev, minCuantia: Number(e.target.value) }))}
            className="px-4 py-2 rounded-full border border-zinc-200 text-zinc-700 bg-white font-medium focus:outline-hidden focus:border-zinc-400"
          >
            <option value={0}>Cualquier cuantía</option>
            <option value={50000}>≥ 50.000 €</option>
            <option value={100000}>≥ 100.000 €</option>
          </select>

          {/* Ordenación */}
          {(modo === 'lista' || modo === 'historico') && (
            <div className="flex items-center gap-1.5 pl-2 border-l border-zinc-200 text-zinc-500">
              <span>Ordenar:</span>
              <select
                value={ordenarPor}
                onChange={(e) => setOrdenarPor(e.target.value as 'matching' | 'cuantia' | 'urgencia')}
                className="px-2 py-1.5 rounded-full border border-zinc-200 text-zinc-800 bg-white font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
              >
                <option value="matching">Mayor encaje</option>
                <option value="cuantia">Mayor cuantía</option>
                <option value="urgencia">{modo === 'historico' ? 'Más recientes' : 'Cierre próximo'}</option>
              </select>
            </div>
          )}

        </div>

      </div>

      {/* Búsquedas rápidas + contador */}
      <div className="max-w-7xl mx-auto mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px]">
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
                className={`px-2.5 py-1 rounded-full border transition-colors ${
                  activo
                    ? 'bg-[#2f6f3e] text-white border-[#2f6f3e] font-semibold'
                    : 'bg-zinc-50 text-zinc-600 border-zinc-200 hover:border-zinc-300 hover:bg-white'
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
            filtros.anio > 0 ||
            filtros.soloUrgentes ||
            filtros.minMatching > 0 ||
            filtros.minCuantia > 0) && (
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
                    anio: 0,
                    soloUrgentes: false,
                    minMatching: 0,
                    minCuantia: 0,
                    ventanaDias: 0,
                  }));
                }
              }}
              className="text-zinc-600 hover:text-zinc-900 underline underline-offset-2"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      </div>

    </div>
  );
}
