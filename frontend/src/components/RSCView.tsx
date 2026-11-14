'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { Building2, ChevronRight } from 'lucide-react';

interface RSCViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function RSCView({ convocatorias, onSeleccionar }: RSCViewProps) {
  const rscConvocatorias = convocatorias.filter((c) => c.tipoFuente === 'privada_rsc');

  return (
    <div className="space-y-4">
      
      {/* Banner Sobrio RSC */}
      <div className="bg-white border border-purple-200 rounded-lg p-4 shadow-2xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-purple-700" />
            <h2 className="text-sm font-bold text-slate-900">Canal de Mecenazgo y Financiación Privada (RSC)</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 max-w-2xl">
            Convocatorias abiertas de fundaciones bancarias y fondos corporativos de sostenibilidad para reforestación y voluntariado.
          </p>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-md px-3 py-1.5 text-center shrink-0">
          <span className="text-[10px] uppercase font-bold text-purple-700 block">Objetivo Reto</span>
          <span className="text-sm font-black text-purple-900">2–4 empresas</span>
        </div>
      </div>

      {/* Grid de Oportunidades RSC */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {rscConvocatorias.map((c) => (
          <div
            key={c.id}
            onClick={() => onSeleccionar(c)}
            className="bg-white border border-slate-200 rounded-lg p-4 hover:border-purple-400 transition-colors cursor-pointer flex flex-col justify-between space-y-3"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-100 flex items-center gap-1">
                  <Building2 className="h-3 w-3" /> {c.organismo}
                </span>
                <span className="bg-emerald-50 text-emerald-800 font-bold px-2 py-0.5 rounded text-xs border border-emerald-200">
                  {c.matchingGlobal}% Match
                </span>
              </div>

              <h3 className="font-bold text-sm text-slate-900 line-clamp-2">{c.titulo}</h3>

              <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{c.resumenEjecutivo}</p>
            </div>

            <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
              <div>
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">Aportación Máxima</span>
                <span className="text-sm font-bold text-slate-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </span>
              </div>

              <button className="px-2.5 py-1 rounded text-xs font-semibold bg-purple-700 text-white hover:bg-purple-800 transition-colors flex items-center gap-1">
                <span>Ver ficha</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}

        {rscConvocatorias.length === 0 && (
          <p className="text-xs text-slate-400 italic p-6 text-center col-span-2 bg-white rounded-lg border border-dashed border-slate-200">
            No hay convocatorias de fondos RSC activas registradas en este momento.
          </p>
        )}
      </div>

    </div>
  );
}
