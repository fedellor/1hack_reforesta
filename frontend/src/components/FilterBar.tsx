'use client';

import React from 'react';
import { Search, SlidersHorizontal, CheckCircle2, ShieldAlert } from 'lucide-react';
import { FiltrosState } from '@/types/convocatoria';

interface FilterBarProps {
  filtros: FiltrosState;
  setFiltros: React.Dispatch<React.SetStateAction<FiltrosState>>;
  ordenarPor: 'matching' | 'cuantia' | 'urgencia';
  setOrdenarPor: (orden: 'matching' | 'cuantia' | 'urgencia') => void;
  totalConvocatorias: number;
  totalFiltradas: number;
}

export function FilterBar({
  filtros,
  setFiltros,
  ordenarPor,
  setOrdenarPor,
  totalConvocatorias,
  totalFiltradas,
}: FilterBarProps) {
  return (
    <div className="bg-white border-b border-slate-200 px-4 sm:px-6 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        
        {/* Input de Búsqueda */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={filtros.busqueda}
            onChange={(e) => setFiltros((prev) => ({ ...prev, busqueda: e.target.value }))}
            placeholder="Buscar por organismo, temática (anfibios, ailanto, riegos) o código..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-slate-50/50"
          />
        </div>

        {/* Filtros Selectores */}
        <div className="flex items-center flex-wrap gap-2">
          
          {/* Selector de Ámbito */}
          <select
            value={filtros.ambito}
            onChange={(e) => setFiltros((prev) => ({ ...prev, ambito: e.target.value }))}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white font-medium focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
          >
            <option value="todos">🌍 Todo el Territorio</option>
            <option value="Estatal">🇪🇸 Ámbito Estatal</option>
            <option value="Madrid">📍 Comunidad de Madrid</option>
            <option value="Galicia">📍 Galicia</option>
            <option value="Castilla y León">📍 Castilla y León</option>
          </select>

          {/* Selector de Tipo de Fuente */}
          <select
            value={filtros.tipoFuente}
            onChange={(e) => setFiltros((prev) => ({ ...prev, tipoFuente: e.target.value }))}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white font-medium focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
          >
            <option value="todos">🏛️ Todas las Fuentes</option>
            <option value="publica_estatal">MITECO / Estatal</option>
            <option value="publica_autonomica">Boletines CCAA (BOCM, DOG...)</option>
            <option value="privada_rsc">Fondos Privados RSC</option>
          </select>

          {/* Toggle Solo Elegibles */}
          <button
            type="button"
            onClick={() => setFiltros((prev) => ({ ...prev, soloElegibles: !prev.soloElegibles }))}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium border transition-colors ${
              filtros.soloElegibles
                ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {filtros.soloElegibles ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            ) : (
              <ShieldAlert className="h-3.5 w-3.5 text-slate-400" />
            )}
            <span>Solo Elegibles (Sin Exclusiones)</span>
          </button>

          {/* Criterio de Ordenación */}
          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
            <span className="text-slate-500 flex items-center gap-1">
              <SlidersHorizontal className="h-3.5 w-3.5" /> Ordenar:
            </span>
            <select
              value={ordenarPor}
              onChange={(e) => setOrdenarPor(e.target.value as any)}
              className="px-2 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white font-semibold focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
            >
              <option value="matching">🎯 Mayor Encaje Reforesta</option>
              <option value="cuantia">💶 Mayor Cuantía (€)</option>
              <option value="urgencia">⏳ Cierre Más Próximo</option>
            </select>
          </div>

        </div>

      </div>

      {/* Contador de resultados */}
      <div className="max-w-7xl mx-auto mt-2 flex items-center justify-between text-[11px] text-slate-500">
        <span>
          Mostrando <strong className="text-slate-800">{totalFiltradas}</strong> de {totalConvocatorias} convocatorias analizadas
        </span>
        {filtros.soloElegibles && (
          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium">
            Filtro de exclusiones activo: descartando automáticamente convocatorias que no admiten ONGs
          </span>
        )}
      </div>

    </div>
  );
}
