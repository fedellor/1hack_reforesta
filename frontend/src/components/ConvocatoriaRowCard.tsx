'use client';

import React from 'react';
import {
  MapPin,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  Mountain,
} from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

interface ConvocatoriaRowCardProps {
  convocatoria: Convocatoria;
  onSeleccionar: (convocatoria: Convocatoria) => void;
  seleccionada?: boolean;
}

export function ConvocatoriaRowCard({
  convocatoria,
  onSeleccionar,
  seleccionada,
}: ConvocatoriaRowCardProps) {
  const c = convocatoria;

  return (
    <div
      onClick={() => onSeleccionar(c)}
      className={`rounded-lg border p-4 transition-all duration-150 cursor-pointer bg-white ${
        seleccionada
          ? 'border-emerald-600 ring-1 ring-emerald-600 shadow-xs'
          : 'border-slate-200 hover:border-slate-400 hover:shadow-2xs'
      } ${!c.elegible ? 'bg-slate-50/60 border-dashed border-rose-200' : ''}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        
        {/* Información Principal */}
        <div className="space-y-1.5 flex-1 min-w-0">
          
          {/* Fila de Metadatos Rápidos */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            <span className="font-mono text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
              {c.codigoOficial}
            </span>

            <span className="text-[11px] font-medium text-slate-600 flex items-center gap-1">
              <MapPin className="h-3 w-3 text-slate-400" />
              {c.ambitoTerritorial}
            </span>

            {/* Orografía / Pendiente (SLOPE) */}
            {c.orografiaPendiente && (
              <span className="text-[11px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded flex items-center gap-1 border border-emerald-100">
                <Mountain className="h-3 w-3 text-emerald-600" />
                {c.orografiaPendiente}
              </span>
            )}

            {/* Urgencia Plazo */}
            <span
              className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                c.diasRestantes <= 7
                  ? 'bg-rose-50 text-rose-700 font-bold border border-rose-200'
                  : c.diasRestantes <= 20
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              Cierre: {c.diasRestantes} días ({new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })})
            </span>
          </div>

          {/* Título de la Convocatoria */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 hover:text-emerald-800 transition-colors line-clamp-1">
              {c.titulo}
            </h3>
            <p className="text-xs text-slate-500 truncate mt-0.5">
              {c.organismo}
            </p>
          </div>

        </div>

        {/* Bloque Económico y Afinidad */}
        <div className="flex items-center justify-between sm:justify-end gap-5 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 shrink-0">
          
          {/* Cuantía */}
          <div className="text-left sm:text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Cuantía Máx.</span>
            <span className="text-base font-extrabold text-slate-900">
              {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                c.cuantiaMaximaProyecto
              )}
            </span>
            <span className="text-[11px] text-slate-500 block">
              {c.porcentajeCofinanciacion === 0 ? '100% subvencionado' : `${100 - c.porcentajeCofinanciacion}% subvención`}
            </span>
          </div>

          {/* Afinidad / Elegibilidad */}
          <div className="text-right">
            <div className="flex items-center justify-end gap-1 mb-0.5">
              {c.elegible ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  <ShieldCheck className="h-3 w-3" /> Apta
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                  <ShieldAlert className="h-3 w-3" /> Excluida
                </span>
              )}

              <span
                className={`text-xs font-bold px-2 py-0.5 rounded ${
                  c.matchingGlobal >= 90
                    ? 'bg-emerald-700 text-white'
                    : c.matchingGlobal >= 80
                    ? 'bg-emerald-100 text-emerald-900'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {c.matchingGlobal}%
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-medium">afinidad Reforesta</span>
          </div>

          {/* Flecha */}
          <div className="hidden sm:block text-slate-400 hover:text-slate-700">
            <ChevronRight className="h-4 w-4" />
          </div>

        </div>

      </div>
    </div>
  );
}
