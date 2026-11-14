'use client';

import React from 'react';
import { Convocatoria, EstadoInterno } from '@/types/convocatoria';
import { Kanban } from 'lucide-react';

interface PipelineViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
  onCambiarEstado: (id: string, nuevoEstado: EstadoInterno) => void;
}

interface ColumnaConfig {
  id: EstadoInterno;
  titulo: string;
  colorBorde: string;
  badgeBg: string;
  badgeText: string;
}

export function PipelineView({ convocatorias, onSeleccionar, onCambiarEstado }: PipelineViewProps) {
  const columnas: ColumnaConfig[] = [
    { id: 'nueva', titulo: '⚪ Nuevas Detectadas', colorBorde: 'border-slate-300', badgeBg: 'bg-slate-100', badgeText: 'text-slate-700' },
    { id: 'priorizada', titulo: '⭐ Priorizadas / Interés', colorBorde: 'border-blue-300', badgeBg: 'bg-blue-100', badgeText: 'text-blue-800' },
    { id: 'en_preparacion', titulo: '✏️ En Preparación', colorBorde: 'border-amber-300', badgeBg: 'bg-amber-100', badgeText: 'text-amber-800' },
    { id: 'presentada', titulo: '✅ Solicitadas / Presentadas', colorBorde: 'border-emerald-300', badgeBg: 'bg-emerald-100', badgeText: 'text-emerald-800' },
    { id: 'descartada', titulo: '❌ Descartadas', colorBorde: 'border-rose-300', badgeBg: 'bg-rose-100', badgeText: 'text-rose-800' },
  ];

  return (
    <div className="space-y-4">
      
      {/* Header del Pipeline */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Kanban className="h-5 w-5 text-emerald-600" />
            Pipeline Operativo del Equipo de Reforesta
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Coordina el flujo de trabajo entre los 6-7 miembros del equipo para no duplicar esfuerzos ni perder plazos.
          </p>
        </div>
        <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
          Objetivo: Pasar de 4-5 a &gt;10 solicitudes/año
        </span>
      </div>

      {/* Columnas Kanban */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 items-start">
        {columnas.map((col) => {
          const items = convocatorias.filter((c) => c.estadoInterno === col.id);
          const totalColumna = items.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);

          return (
            <div
              key={col.id}
              className={`bg-slate-100/70 border ${col.colorBorde} rounded-xl p-3 flex flex-col space-y-2.5 min-h-[500px]`}
            >
              {/* Header de Columna */}
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                <span className="font-bold text-xs text-slate-800">{col.titulo}</span>
                <span className={`text-[10px] font-bold px-2 py-0.2 rounded-full ${col.badgeBg} ${col.badgeText}`}>
                  {items.length}
                </span>
              </div>

              {/* Total económico de la columna */}
              {items.length > 0 && (
                <div className="text-[10px] text-slate-500 font-medium pb-1">
                  Volumen:{' '}
                  <strong className="text-slate-800">
                    {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                      totalColumna
                    )}
                  </strong>
                </div>
              )}

              {/* Tarjetas de la Columna */}
              <div className="space-y-2 flex-1">
                {items.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => onSeleccionar(c)}
                    className="bg-white border border-slate-200 rounded-lg p-3 hover:border-emerald-400 hover:shadow-xs transition-all cursor-pointer space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[9px] font-bold text-slate-500">{c.codigoOficial}</span>
                      <span className="bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.2 rounded text-[10px]">
                        {c.matchingGlobal}%
                      </span>
                    </div>

                    <h4 className="font-bold text-slate-900 line-clamp-2 leading-snug">{c.titulo}</h4>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                      <span className="font-black text-slate-800">
                        {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                          c.cuantiaMaximaProyecto
                        )}
                      </span>
                      <span
                        className={`font-semibold ${
                          c.diasRestantes <= 7 ? 'text-rose-600' : 'text-slate-500'
                        }`}
                      >
                        {c.diasRestantes}d
                      </span>
                    </div>

                    {/* Mover rápido a siguiente estado */}
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="pt-1.5 flex items-center justify-between text-[10px] border-t border-slate-100"
                    >
                      <span className="text-slate-400">Mover:</span>
                      <select
                        value={c.estadoInterno}
                        onChange={(e) => onCambiarEstado(c.id, e.target.value as EstadoInterno)}
                        className="bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 text-slate-700 text-[10px] font-medium"
                      >
                        <option value="nueva">Nueva</option>
                        <option value="priorizada">Priorizada</option>
                        <option value="en_preparacion">En prep.</option>
                        <option value="presentada">Presentada</option>
                        <option value="descartada">Descartada</option>
                      </select>
                    </div>
                  </div>
                ))}

                {items.length === 0 && (
                  <div className="h-24 flex items-center justify-center text-slate-400 text-[11px] italic border border-dashed border-slate-300 rounded-lg">
                    Sin convocatorias
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
