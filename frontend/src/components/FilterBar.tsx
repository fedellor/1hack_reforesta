'use client';

import React from 'react';
import { Search, CheckCircle2 } from 'lucide-react';
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
    <div className="bg-slate-50/70 border-b border-slate-200 px-4 sm:px-6 lg:px-8 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 text-xs">
        
        {/* Buscador de Texto */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={filtros.busqueda}
            onChange={(e) => setFiltros((prev) => ({ ...prev, busqueda: e.target.value }))}
            placeholder="Buscar por código, organismo o palabra clave..."
            className="w-full pl-8 pr-3 py-1.5 rounded-md border border-slate-300 text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-emerald-600 focus:border-emerald-600 bg-white"
          />
        </div>

        {/* Controles de Filtro */}
        <div className="flex items-center flex-wrap gap-2">
          
          {/* Ámbito */}
          <select
            value={filtros.ambito}
            onChange={(e) => setFiltros((prev) => ({ ...prev, ambito: e.target.value }))}
            className="px-2.5 py-1.5 rounded-md border border-slate-300 text-slate-700 bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-600 font-medium"
          >
            <option value="todos">Todo el Territorio</option>
            <option value="Estatal">Ámbito Estatal</option>
            <option value="Madrid">Comunidad de Madrid</option>
            <option value="Galicia">Galicia</option>
            <option value="Castilla y León">Castilla y León</option>
          </select>

          {/* Tipo de Fuente */}
          <select
            value={filtros.tipoFuente}
            onChange={(e) => setFiltros((prev) => ({ ...prev, tipoFuente: e.target.value }))}
            className="px-2.5 py-1.5 rounded-md border border-slate-300 text-slate-700 bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-600 font-medium"
          >
            <option value="todos">Todas las Fuentes</option>
            <option value="publica_estatal">Estatal (MITECO)</option>
            <option value="publica_autonomica">Autonómica (CCAA)</option>
            <option value="privada_rsc">Privada (RSC)</option>
          </select>

          {/* Solo Elegibles Toggle */}
          <button
            type="button"
            onClick={() => setFiltros((prev) => ({ ...prev, soloElegibles: !prev.soloElegibles }))}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md font-medium border transition-colors ${
              filtros.soloElegibles
                ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold'
                : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            <span>Solo Elegibles</span>
          </button>

          {/* Ordenar */}
          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-200">
            <span className="text-slate-500">Ordenar:</span>
            <select
              value={ordenarPor}
              onChange={(e) => setOrdenarPor(e.target.value as 'matching' | 'cuantia' | 'urgencia')}
              className="px-2 py-1.5 rounded-md border border-slate-300 text-slate-800 bg-white font-medium focus:outline-hidden focus:ring-1 focus:ring-emerald-600"
            >
              <option value="matching">Mayor Encaje</option>
              <option value="cuantia">Mayor Cuantía</option>
              <option value="urgencia">Cierre Próximo</option>
            </select>
          </div>

        </div>

      </div>

      <div className="max-w-7xl mx-auto mt-1.5 flex items-center justify-between text-[11px] text-slate-500">
        <span>{totalFiltradas} de {totalConvocatorias} convocatorias</span>
        {filtros.soloElegibles && (
          <span className="text-slate-400">Descartadas automáticamente convocatorias que no admiten ONGs</span>
        )}
      </div>
    </div>
  );
}
