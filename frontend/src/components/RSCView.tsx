'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { Building2, Sparkles, Handshake, ExternalLink, ShieldCheck, ChevronRight } from 'lucide-react';

interface RSCViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function RSCView({ convocatorias, onSeleccionar }: RSCViewProps) {
  const rscConvocatorias = convocatorias.filter((c) => c.tipoFuente === 'privada_rsc');

  return (
    <div className="space-y-6">
      
      {/* Banner de Impacto RSC */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-400/20 text-purple-200 border border-purple-400/30">
              Objetivo del Reto: Reactivación Canal Empresas (RSC/ESG)
            </span>
            <h2 className="text-lg font-bold">Oportunidades de Financiación Privada y Mecenazgo</h2>
            <p className="text-xs text-purple-200 max-w-2xl">
              Actualmente este canal está a cero en Reforesta porque solo atienden a las empresas que les buscan a ellos.
              Aquí se monitorizan convocatorias abiertas de fundaciones bancarias y fondos corporativos de sostenibilidad.
            </p>
          </div>

          <div className="bg-purple-800/60 border border-purple-500/30 rounded-xl p-3 text-center shrink-0">
            <span className="text-[10px] uppercase font-bold text-purple-300">Meta del Reto</span>
            <p className="text-xl font-black text-white">2–4</p>
            <span className="text-[10px] text-purple-200">Primeras empresas captadas</span>
          </div>
        </div>
      </div>

      {/* Grid de Oportunidades RSC */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rscConvocatorias.map((c) => (
          <div
            key={c.id}
            onClick={() => onSeleccionar(c)}
            className="bg-white border border-purple-200 rounded-xl p-5 hover:border-purple-500 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200 flex items-center gap-1">
                  <Building2 className="h-3 w-3" /> {c.organismo}
                </span>
                <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded text-xs">
                  {c.matchingGlobal}% Match
                </span>
              </div>

              <h3 className="font-bold text-sm text-slate-900 line-clamp-2">{c.titulo}</h3>

              <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{c.resumenEjecutivo}</p>

              <div className="bg-purple-50/50 p-2.5 rounded-lg border border-purple-100 text-xs text-purple-900 space-y-1">
                <p className="font-semibold text-[11px] uppercase tracking-wide text-purple-700">Modelo de Cooperación:</p>
                <p className="text-slate-700">{c.accionesSubvencionables[0] || 'Financiación 100% directa por hectárea restaurada.'}</p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <div>
                <span className="text-[10px] uppercase text-slate-400 font-semibold">Aportación Máxima</span>
                <p className="text-base font-black text-slate-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </p>
              </div>

              <button className="px-3 py-1.5 rounded-lg font-semibold bg-purple-600 text-white hover:bg-purple-700 transition-colors flex items-center gap-1">
                <span>Ficha de Captación</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}

        {rscConvocatorias.length === 0 && (
          <p className="text-xs text-slate-400 italic p-6 text-center col-span-2 bg-white rounded-xl border border-dashed border-slate-200">
            No hay convocatorias de fondos RSC activas registradas en este momento.
          </p>
        )}
      </div>

    </div>
  );
}
