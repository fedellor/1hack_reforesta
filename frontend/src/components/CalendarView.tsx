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

  const renderGrupo = (titulo: string, lista: Convocatoria[], badgeColor: string) => {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className={`h-3 w-3 rounded-full ${badgeColor}`} />
          <h3 className="font-bold text-slate-800 text-sm">{titulo}</h3>
          <span className="text-xs text-slate-400">({lista.length})</span>
        </div>

        <div className="space-y-2">
          {lista.map((c) => (
            <div
              key={c.id}
              onClick={() => onSeleccionar(c)}
              className="bg-white border border-slate-200 rounded-xl p-3.5 hover:border-emerald-400 hover:shadow-xs transition-all cursor-pointer flex items-center justify-between gap-4"
            >
              <div className="flex items-start gap-3">
                <div className="text-center bg-slate-50 border border-slate-200 rounded-lg p-2 min-w-[55px] shrink-0">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    {new Date(c.fechaCierre).toLocaleDateString('es-ES', { month: 'short' })}
                  </span>
                  <p className="text-base font-black text-slate-800">
                    {new Date(c.fechaCierre).getDate()}
                  </p>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-[10px] font-bold text-slate-500">{c.codigoOficial}</span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-600 font-medium">{c.ambitoTerritorial}</span>
                  </div>
                  <h4 className="font-bold text-xs text-slate-900 line-clamp-1">{c.titulo}</h4>
                  <p className="text-[11px] text-slate-500 font-medium">
                    Hasta {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(c.cuantiaMaximaProyecto)}
                    {' · '}
                    <span className="text-emerald-700 font-semibold">{c.matchingGlobal}% Match</span>
                  </p>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    c.diasRestantes <= 7
                      ? 'bg-rose-100 text-rose-800'
                      : c.diasRestantes <= 20
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {c.diasRestantes} días restantes
                </span>
              </div>
            </div>
          ))}
          {lista.length === 0 && (
            <p className="text-xs text-slate-400 italic bg-slate-50 p-3 rounded-lg border border-dashed border-slate-200">
              No hay convocatorias en este rango temporal.
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-900 flex items-start gap-3">
        <Clock className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-sm">Cronograma y Planificación de Entregas</h4>
          <p className="text-emerald-800 mt-0.5">
            Organiza el esfuerzo del equipo según la cercanía de la fecha límite para no perder ninguna oportunidad crítica.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {renderGrupo('🔥 Vencimiento Crítico (≤ 10 días)', urgentes, 'bg-rose-500')}
        {renderGrupo('⏳ Próximas a Vencer (11 - 25 días)', proximas, 'bg-amber-500')}
        {renderGrupo('📅 Horizonte Amplio (&gt; 25 días)', horizonte, 'bg-emerald-500')}
      </div>
    </div>
  );
}
