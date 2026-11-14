'use client';

import React from 'react';
import { ChevronRight } from 'lucide-react';
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
      className={`rounded-lg border p-3.5 transition-all duration-150 cursor-pointer bg-white group ${
        seleccionada
          ? 'border-zinc-900 ring-1 ring-zinc-900 shadow-2xs'
          : 'border-zinc-200 hover:border-zinc-400 hover:bg-zinc-50/50'
      } ${!c.elegible ? 'bg-zinc-50/60 opacity-70 border-dashed' : ''}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        
        {/* Información Principal */}
        <div className="space-y-1 flex-1 min-w-0">
          
          {/* Fila de Metadatos: Código, Territorio y Orografía */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            <span className="font-mono text-[11px] text-zinc-500 font-medium">
              {c.codigoOficial}
            </span>
            <span className="text-zinc-300">·</span>
            <span className="text-zinc-600 text-[11px]">
              {c.ambitoTerritorial}
            </span>

            {c.orografiaPendiente && (
              <>
                <span className="text-zinc-300">·</span>
                <span className="text-[11px] text-zinc-600 font-medium">
                  {c.orografiaPendiente}
                </span>
              </>
            )}

            <span className="text-zinc-300">·</span>
            <span
              className={`text-[11px] font-medium ${
                c.diasRestantes <= 7
                  ? 'text-rose-700 font-semibold'
                  : c.diasRestantes <= 20
                  ? 'text-amber-700'
                  : 'text-zinc-500'
              }`}
            >
              Cierre: {c.diasRestantes}d ({new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })})
            </span>
          </div>

          {/* Título de la Convocatoria */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-900 group-hover:text-emerald-900 transition-colors line-clamp-1">
              {c.titulo}
            </h3>
            <p className="text-xs text-zinc-500 truncate mt-0.5">
              {c.organismo}
            </p>
            {(c.elegible ? c.citasBasesJustificacion[0] : c.dealbreakers[0] ?? c.motivoElegibilidad) && (
              <p className={`text-[11px] italic line-clamp-1 mt-1 border-l-2 pl-2 ${c.elegible ? 'border-brand text-zinc-500' : 'border-rose-400 text-rose-700'}`}>
                {c.elegible ? `“${c.citasBasesJustificacion[0]}”` : `Excluida: ${c.dealbreakers[0] ?? c.motivoElegibilidad}`}
              </p>
            )}
          </div>

        </div>

        {/* Bloque Económico y Afinidad */}
        <div className="flex items-center justify-between sm:justify-end gap-6 pt-2 sm:pt-0 border-t sm:border-t-0 border-zinc-100 shrink-0">
          
          {/* Cuantía */}
          <div className="text-left sm:text-right">
            <span className="text-sm font-bold text-zinc-900 font-mono block">
              {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                c.cuantiaMaximaProyecto
              )}
            </span>
            <span className="text-[11px] text-zinc-400 block">
              {c.porcentajeCofinanciacion === 0 ? '100% subvencionado' : `${c.porcentajeCofinanciacion}% fondos propios`} · {c.modalidadPago}
            </span>
          </div>

          {/* Afinidad por línea */}
          <div className="hidden md:flex flex-col gap-1 w-28">
            {[
              ['Restauración', c.matchingLineas.restauracionEcosistemas],
              ['Hábitats', c.matchingLineas.conservacionHabitats],
              ['Educación', c.matchingLineas.educacionAmbiental],
            ].map(([nombre, valor]) => (
              <div key={nombre} className="flex items-center gap-1.5 text-[10px] text-zinc-500">
                <span className="w-14 truncate">{nombre}</span>
                <span className="flex-1 h-1 rounded-full bg-zinc-100 overflow-hidden">
                  <span className="block h-full bg-brand" style={{ width: `${valor}%` }} />
                </span>
              </div>
            ))}
          </div>

          {/* Estado de Elegibilidad y Afinidad */}
          <div className="text-right flex items-center gap-3">
            <div>
              <div className="flex items-center justify-end gap-1.5">
                <span
                  className={`h-2 w-2 rounded-full ${
                    c.elegible ? 'bg-emerald-600' : 'bg-rose-500'
                  }`}
                />
                <span className="text-xs font-semibold text-zinc-900 font-mono">
                  {c.matchingGlobal}%
                </span>
              </div>
              <span className="text-[10px] text-zinc-400 block">
                {c.elegible ? 'Apta' : 'Excluida'}
              </span>
            </div>

            <ChevronRight className="h-4 w-4 text-zinc-400 group-hover:text-zinc-700 transition-colors" />
          </div>

        </div>

      </div>
    </div>
  );
}
