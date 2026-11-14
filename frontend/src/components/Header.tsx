'use client';

import React from 'react';
import { TreePine, RefreshCw } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

interface HeaderProps {
  convocatorias: Convocatoria[];
  vistaActiva: 'tarjetas' | 'tabla' | 'pipeline' | 'mapa' | 'rsc';
  setVistaActiva: (vista: 'tarjetas' | 'tabla' | 'pipeline' | 'mapa' | 'rsc') => void;
  onRefresh?: () => void;
}

export function Header({ convocatorias, vistaActiva, setVistaActiva, onRefresh }: HeaderProps) {
  const aptas = convocatorias.filter((c) => c.elegible);
  const totalFondos = aptas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);
  const urgentes = aptas.filter((c) => c.diasRestantes <= 15).length;
  const privadasRSC = aptas.filter((c) => c.tipoFuente === 'privada_rsc').length;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Fila Principal: Marca y KPIs Rápidos */}
        <div className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100">
          
          {/* Logo Reforesta y Título */}
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-700 flex items-center justify-center text-white shrink-0">
              <TreePine className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-900 tracking-tight">
                  Radar Reforesta
                </h1>
                <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  Panel de Financiación
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Monitoreo y evaluación de convocatorias públicas y privadas para restauración ambiental
              </p>
            </div>
          </div>

          {/* KPIs Sobrios y Compactos */}
          <div className="flex items-center flex-wrap gap-4 text-xs">
            <div className="border-r border-slate-200 pr-4">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Fondos Aptos</span>
              <span className="text-sm font-bold text-slate-900">
                {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(totalFondos)}
              </span>
            </div>

            <div className="border-r border-slate-200 pr-4">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Convocatorias</span>
              <span className="text-sm font-bold text-emerald-700">{aptas.length} activas</span>
            </div>

            <div className="border-r border-slate-200 pr-4">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Cierre &lt; 15d</span>
              <span className="text-sm font-bold text-amber-700">{urgentes} urgentes</span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Canal RSC</span>
              <span className="text-sm font-bold text-purple-700">{privadasRSC} empresas</span>
            </div>
          </div>

        </div>

        {/* Fila de Navegación por Vistas */}
        <div className="py-2 flex items-center justify-between gap-2 overflow-x-auto text-xs">
          <nav className="flex items-center space-x-1">
            <button
              onClick={() => setVistaActiva('tarjetas')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                vistaActiva === 'tarjetas'
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Listado
            </button>
            <button
              onClick={() => setVistaActiva('tabla')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                vistaActiva === 'tabla'
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Tabla Técnica
            </button>
            <button
              onClick={() => setVistaActiva('pipeline')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                vistaActiva === 'pipeline'
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Pipeline Kanban
            </button>
            <button
              onClick={() => setVistaActiva('mapa')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                vistaActiva === 'mapa'
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Mapa Territorial
            </button>
            <button
              onClick={() => setVistaActiva('rsc')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                vistaActiva === 'rsc'
                  ? 'bg-purple-700 text-white font-semibold'
                  : 'text-purple-700 hover:bg-purple-50'
              }`}
            >
              Empresas RSC
            </button>
          </nav>

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-[11px] text-slate-500 hover:text-slate-800 flex items-center gap-1.5 px-2 py-1 rounded transition-colors"
              title="Actualizar datos con las fuentes oficiales"
            >
              <RefreshCw className="h-3 w-3" />
              <span className="hidden sm:inline">Actualizado hoy</span>
            </button>
          )}
        </div>

      </div>
    </header>
  );
}
