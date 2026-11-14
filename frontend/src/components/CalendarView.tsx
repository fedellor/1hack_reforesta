'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { Clock } from 'lucide-react';

interface CalendarViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function CalendarView({ convocatorias, onSeleccionar }: CalendarViewProps) {
  // Ordenar por fecha de cierre ascendente
  const ordenadas = [...convocatorias].sort(
    (a, b) => new Date(a.fechaCierre).getTime() - new Date(b.fechaCierre).getTime()
  );

  const urgentes = ordenadas.filter((c) => c.diasRestantes <= 10);
  const proximas = ordenadas.filter((c) => c.diasRestantes > 10 && c.diasRestantes <= 25);
  const horizonte = ordenadas.filter((c) => c.diasRestantes > 25);

  const renderGrupo = (titulo: string, lista: Convocatoria[], dotColor: string) => {
    return (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2 border-b border-zinc-200 pb-1.5">
          <span className={`h-2 w-2 rounded-full ${dotColor}`} />
          <h3 className="font-bold text-zinc-900 text-xs uppercase tracking-wider">{titulo}</h3>
          <span className="text-xs text-zinc-400">({lista.length})</span>
        </div>

        <div className="space-y-2">
          {lista.map((c) => (
            <div
              key={c.id}
              onClick={() => onSeleccionar(c)}
              className="bg-white border border-zinc-200 rounded-lg p-3 hover:border-zinc-400 transition-colors cursor-pointer flex items-center justify-between gap-3 text-xs"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="text-center font-mono bg-zinc-50 border border-zinc-200 rounded p-1.5 min-w-[46px] shrink-0">
                  <span className="text-[9px] uppercase font-semibold text-zinc-400 block">
                    {new Date(c.fechaCierre).toLocaleDateString('es-ES', { month: 'short' })}
                  </span>
                  <span className="text-sm font-bold text-zinc-900 block leading-none mt-0.5">
                    {new Date(c.fechaCierre).getDate()}
                  </span>
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-[11px] text-zinc-500 mb-0.5">
                    <span className="font-mono font-medium">{c.codigoOficial}</span>
                    <span>·</span>
                    <span>{c.ambitoTerritorial}</span>
                  </div>
                  <h4 className="font-bold text-zinc-900 truncate">{c.titulo}</h4>
                  <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                    {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                      c.cuantiaMaximaProyecto
                    )}
                  </p>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span
                  className={`font-semibold font-mono text-xs ${
                    c.diasRestantes <= 7
                      ? 'text-rose-700'
                      : c.diasRestantes <= 20
                      ? 'text-amber-800'
                      : 'text-zinc-600'
                  }`}
                >
                  {c.diasRestantes}d
                </span>
              </div>
            </div>
          ))}

          {lista.length === 0 && (
            <p className="text-xs text-zinc-400 italic bg-white p-3 rounded-lg border border-dashed border-zinc-200">
              No hay convocatorias en este rango.
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="bg-white border border-zinc-200 rounded-lg p-3.5 flex items-center justify-between text-xs text-zinc-600">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-zinc-700 shrink-0" />
          <span>Cronograma de fechas límite para la planificación del equipo</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {renderGrupo('Vencimiento Crítico (≤ 10 días)', urgentes, 'bg-rose-500')}
        {renderGrupo('Próximas a Vencer (11 - 25 días)', proximas, 'bg-amber-500')}
        {renderGrupo('Horizonte Abierto (> 25 días)', horizonte, 'bg-emerald-600')}
      </div>
    </div>
  );
}
