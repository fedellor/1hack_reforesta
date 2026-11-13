'use client';

import React from 'react';
import { TreePine, Euro, Target, AlertTriangle, Building2, RefreshCw } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

interface HeaderProps {
  convocatorias: Convocatoria[];
  vistaActiva: 'tarjetas' | 'tabla' | 'calendario' | 'mapa' | 'rsc';
  setVistaActiva: (vista: 'tarjetas' | 'tabla' | 'calendario' | 'mapa' | 'rsc') => void;
  onRefresh?: () => void;
}

export function Header({ convocatorias, vistaActiva, setVistaActiva, onRefresh }: HeaderProps) {
  const aptas = convocatorias.filter((c) => c.elegible);
  const totalFondos = aptas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);
  const urgentes = aptas.filter((c) => c.diasRestantes <= 15).length;
  const privadasRSC = aptas.filter((c) => c.tipoFuente === 'privada_rsc').length;

  return (
    <header className="border-b border-emerald-900/20 bg-gradient-to-r from-emerald-950 via-slate-900 to-emerald-950 text-white shadow-lg sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Logo y Titular */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-green-600 flex items-center justify-center shadow-md shadow-emerald-500/20">
              <TreePine className="h-6 w-6 text-emerald-950" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                  Radar Reforesta
                </h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30">
                  Consola de Financiación
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Observatorio inteligente de convocatorias y captación de fondos para restauración ecológica
              </p>
            </div>
          </div>

          {/* KPIs en Tiempo Real */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            
            {/* Total Fondos */}
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2.5">
              <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400">
                <Euro className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] uppercase font-semibold text-slate-400">Fondos Aptos</p>
                <p className="font-bold text-sm text-emerald-400">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(totalFondos)}
                </p>
              </div>
            </div>

            {/* Convocatorias Aptas */}
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2.5">
              <div className="p-1.5 rounded-md bg-blue-500/20 text-blue-400">
                <Target className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] uppercase font-semibold text-slate-400">Oportunidades</p>
                <p className="font-bold text-sm text-blue-300">{aptas.length} activas</p>
              </div>
            </div>

            {/* Urgentes */}
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2.5">
              <div className="p-1.5 rounded-md bg-amber-500/20 text-amber-400">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] uppercase font-semibold text-slate-400">Próx. Cierre</p>
                <p className="font-bold text-sm text-amber-300">{urgentes} (&lt;15 días)</p>
              </div>
            </div>

            {/* Oportunidades RSC */}
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2.5">
              <div className="p-1.5 rounded-md bg-purple-500/20 text-purple-400">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] uppercase font-semibold text-slate-400">Canal RSC</p>
                <p className="font-bold text-sm text-purple-300">{privadasRSC} empresas</p>
              </div>
            </div>

          </div>

        </div>

        {/* Barra de Navegación de Vistas */}
        <div className="mt-3.5 pt-2.5 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-2">
          <nav className="flex items-center space-x-1 sm:space-x-2 text-xs">
            <button
              onClick={() => setVistaActiva('tarjetas')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                vistaActiva === 'tarjetas'
                  ? 'bg-emerald-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              📊 Fichas Inteligentes
            </button>
            <button
              onClick={() => setVistaActiva('tabla')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                vistaActiva === 'tabla'
                  ? 'bg-emerald-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              📋 Tabla Técnica
            </button>
            <button
              onClick={() => setVistaActiva('calendario')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                vistaActiva === 'calendario'
                  ? 'bg-emerald-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              📅 Calendario Deadlines
            </button>
            <button
              onClick={() => setVistaActiva('mapa')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                vistaActiva === 'mapa'
                  ? 'bg-emerald-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              🗺️ Vista Territorial
            </button>
            <button
              onClick={() => setVistaActiva('rsc')}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                vistaActiva === 'rsc'
                  ? 'bg-purple-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-purple-300 hover:text-white hover:bg-purple-900/30'
              }`}
            >
              🏢 Canal Empresas RSC
            </button>
          </nav>

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1.5 transition-colors px-2.5 py-1 rounded-md hover:bg-slate-800"
              title="Sincronizar convocatorias con fuentes oficiales"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Sincronizado hoy</span>
            </button>
          )}
        </div>

      </div>
    </header>
  );
}
