'use client';

import React from 'react';
import { Search } from 'lucide-react';
import { FiltrosState } from '@/types/convocatoria';
import { COMUNIDADES } from '@/lib/territorio';

interface FilterBarProps {
  filtros: FiltrosState;
  setFiltros: React.Dispatch<React.SetStateAction<FiltrosState>>;
  ordenarPor: 'matching' | 'cuantia' | 'urgencia';
  setOrdenarPor: (orden: 'matching' | 'cuantia' | 'urgencia') => void;
  /** Qué controles tienen sentido en cada sección */
  modo: 'mapa' | 'lista' | 'calendario';
}

export function FilterBar({
  filtros,
  setFiltros,
  ordenarPor,
  setOrdenarPor,
  modo,
}: FilterBarProps) {
  const chip = (activo: boolean) =>
    `px-5 py-2.5 rounded-full border font-semibold uppercase text-xs tracking-wide transition-colors ${
      activo ? 'bg-brand border-brand text-white' : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'
    }`;
  return (
    <div className="bg-zinc-50/80 border-b border-zinc-200 px-4 sm:px-6 lg:px-8 py-4">
      <div className="max-w-[1300px] mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        
        {/* Input de Búsqueda */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            value={filtros.busqueda}
            onChange={(e) => setFiltros((prev) => ({ ...prev, busqueda: e.target.value }))}
            placeholder="Filtrar por código, organismo, pendiente o término..."
            className="w-full pl-9 pr-4 py-2 rounded-full border border-zinc-200 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:border-zinc-400 bg-white text-xs shadow-2xs"
          />
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
            {filtros.soloElegibles ? 'Solo aptas' : 'Todas (incl. excluidas)'}
          </button>

          {/* Ventana de 30 días */}
          {modo !== 'calendario' && <button
            type="button"
            onClick={() => setFiltros((prev) => ({ ...prev, ventanaDias: prev.ventanaDias === 30 ? 0 : 30 }))}
            className={chip(filtros.ventanaDias === 30)}
          >
            Cierre ≤ 30 días
          </button>}

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
          {modo === 'lista' && <div className="flex items-center gap-1.5 pl-2 border-l border-zinc-200 text-zinc-500">
            <span>Ordenar:</span>
            <select
              value={ordenarPor}
              onChange={(e) => setOrdenarPor(e.target.value as 'matching' | 'cuantia' | 'urgencia')}
              className="px-2 py-1.5 rounded-full border border-zinc-200 text-zinc-800 bg-white font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
            >
              <option value="matching">Mayor encaje</option>
              <option value="cuantia">Mayor cuantía</option>
              <option value="urgencia">Cierre próximo</option>
            </select>
          </div>}

        </div>

      </div>

    </div>
  );
}
