'use client';

import React, { useState } from 'react';
import { Convocatoria, EstadoInterno } from '@/types/convocatoria';

interface PipelineViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
  onCambiarEstado: (id: string, nuevoEstado: EstadoInterno) => void;
}

interface ColumnaConfig {
  id: EstadoInterno;
  titulo: string;
  dotColor: string;
}

export function PipelineView({ convocatorias, onSeleccionar, onCambiarEstado }: PipelineViewProps) {
  const [abiertas, setAbiertas] = useState<Record<string, boolean>>({});
  const TOPE = 5;
  const columnas: ColumnaConfig[] = [
    { id: 'nueva', titulo: 'Nuevas', dotColor: 'bg-zinc-400' },
    { id: 'priorizada', titulo: 'Priorizadas', dotColor: 'bg-blue-600' },
    { id: 'en_preparacion', titulo: 'En Preparación', dotColor: 'bg-amber-600' },
    { id: 'presentada', titulo: 'Presentadas', dotColor: 'bg-emerald-600' },
    { id: 'descartada', titulo: 'Descartadas', dotColor: 'bg-rose-600' },
  ];

  return (
    <div className="space-y-4">
      
      {/* Columnas Kanban */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-start">
        {columnas.map((col) => {
          const todas = convocatorias.filter((c) => c.estadoInterno === col.id).sort((a, b) => a.diasRestantes - b.diasRestantes);
          const items = abiertas[col.id] ? todas : todas.slice(0, TOPE);
          const totalColumna = todas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);

          return (
            <div
              key={col.id}
              className="bg-zinc-100/70 border border-zinc-200/80 rounded-none p-2.5 flex flex-col space-y-2 min-h-[200px]"
            >
              {/* Header de Columna */}
              <div className="flex items-center justify-between border-b border-zinc-200 pb-1.5">
                <div className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${col.dotColor}`} />
                  <span className="font-semibold text-xs text-zinc-800">{col.titulo}</span>
                </div>
                <span className="text-[11px] font-semibold text-zinc-500 bg-white px-1.5 py-0.2 rounded border border-zinc-200">
                  {todas.length}
                </span>
              </div>

              {/* Total económico */}
              {todas.length > 0 && (
                <div className="text-[11px] text-zinc-500 pb-0.5">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    totalColumna
                  )}
                </div>
              )}

              {/* Tarjetas */}
              <div className="space-y-1.5 flex-1">
                {items.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => onSeleccionar(c)}
                    className="bg-white border border-zinc-200 rounded-md p-2.5 hover:border-zinc-400 transition-colors cursor-pointer space-y-1.5 text-xs shadow-2xs"
                  >
                    <div className="flex items-center justify-between text-[11px] text-zinc-500">
                      <span className="font-mono">{c.codigoOficial}</span>
                      <span className="font-bold text-zinc-700">{c.matchingGlobal}%</span>
                    </div>

                    <h4 className="font-bold text-zinc-900 line-clamp-2 leading-tight">{c.titulo}</h4>

                    <div className="flex items-center justify-between pt-1 border-t border-zinc-100 text-xs">
                      <span className="font-bold text-zinc-900">
                        {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                          c.cuantiaMaximaProyecto
                        )}
                      </span>
                      <span className={c.diasRestantes < 7 ? 'text-rose-700 font-bold' : c.diasRestantes < 20 ? 'text-amber-700 font-semibold' : 'text-zinc-500'}>
                        cierra en {c.diasRestantes} d
                      </span>
                    </div>

                    {/* Selector de estado */}
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="pt-1 flex items-center justify-between text-[11px] border-t border-zinc-100"
                    >
                      <span className="text-zinc-400">Estado:</span>
                      <select
                        value={c.estadoInterno}
                        onChange={(e) => onCambiarEstado(c.id, e.target.value as EstadoInterno)}
                        className="bg-zinc-50 border border-zinc-200 rounded px-1.5 py-0.5 text-zinc-700 text-[11px] font-medium"
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

                {todas.length > TOPE && (
                  <button
                    onClick={() => setAbiertas((p) => ({ ...p, [col.id]: !p[col.id] }))}
                    className="w-full py-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-900"
                  >
                    {abiertas[col.id] ? 'Ver menos' : `Ver ${todas.length - TOPE} más`}
                  </button>
                )}

                {todas.length === 0 && (
                  <div className="h-20 flex items-center justify-center text-zinc-400 text-xs italic border border-dashed border-zinc-200 rounded">
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
