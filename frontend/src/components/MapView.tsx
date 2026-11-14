'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Convocatoria } from '@/types/convocatoria';
import { ChevronRight } from 'lucide-react';
import { TODOS, formatoEuros } from '@/lib/territorio';

// Cargar Leaflet dinámicamente sin SSR para evitar errores de window en Next.js
const LeafletMap = dynamic(() => import('@/components/LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[520px] rounded-lg border border-zinc-200 bg-zinc-50 flex items-center justify-center text-xs text-zinc-400">
      Cargando cartografía oficial...
    </div>
  ),
});

interface MapViewProps {
  /** Lista SIN filtrar por territorio: colorea el mapa */
  convocatorias: Convocatoria[];
  /** Lista ya filtrada (incluido el territorio): se muestra al lado */
  filtradas: Convocatoria[];
  territorio: string;
  onCambiarTerritorio: (territorio: string) => void;
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function MapView({ convocatorias, filtradas, territorio, onCambiarTerritorio, onSeleccionar }: MapViewProps) {
  const convocatoriasFiltradas = filtradas;
  const totalPresupuesto = convocatoriasFiltradas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);
  const territorioActivo = territorio;

  return (
    <div className="space-y-4">
      
      {/* Grid: Mapa Leaflet Real + Listado Lateral */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        
        {/* Columna Mapa */}
        <div className="lg:col-span-7">
          <LeafletMap
            convocatorias={convocatorias}
            territorio={territorio}
            onCambiarTerritorio={onCambiarTerritorio}
          />
        </div>

        {/* Columna Convocatorias del Área */}
        <div className="lg:col-span-5 space-y-2.5">
          
          <div className="bg-white border border-zinc-200 rounded-lg p-3 flex items-center justify-between text-xs">
            <div>
              <span className="text-[10px] text-zinc-400 uppercase font-medium block">Territorio</span>
              <span className="font-semibold text-zinc-900">
                {territorioActivo === TODOS ? 'España (todas)' : territorioActivo}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-zinc-400 uppercase font-medium block">Total Disponible</span>
              <span className="font-bold text-zinc-900">
                {formatoEuros(totalPresupuesto)}
              </span>
            </div>
          </div>

          <div className="space-y-2 max-h-[448px] overflow-y-auto pr-1">
            {convocatoriasFiltradas.map((c) => (
              <div
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="bg-white border border-zinc-200 rounded-lg p-3 hover:border-zinc-400 transition-colors cursor-pointer group space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-[10px] text-zinc-500">{c.codigoOficial}</span>
                  <div className="flex items-center gap-1.5">
                    {c.elegible ? (
                      <span className="text-[10px] text-emerald-700 font-medium">Apta</span>
                    ) : (
                      <span className="text-[10px] text-rose-600 font-medium">Excluida</span>
                    )}
                    <span className="text-[10px] font-mono text-zinc-600 font-bold bg-zinc-100 px-1.5 py-0.2 rounded">
                      {c.matchingGlobal}%
                    </span>
                  </div>
                </div>

                <h4 className="text-xs font-semibold text-zinc-900 group-hover:text-emerald-800 transition-colors line-clamp-2">
                  {c.titulo}
                </h4>

                <p className="text-[11px] text-zinc-500 truncate">{c.organismo}</p>

                <div className="flex items-center justify-between pt-1.5 border-t border-zinc-100 text-xs">
                  <span className="font-bold text-zinc-900">
                    {formatoEuros(c.cuantiaMaximaProyecto)}
                  </span>
                  <span className="text-[11px] text-zinc-500 group-hover:text-zinc-900 flex items-center gap-0.5">
                    Ficha <ChevronRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white border border-dashed border-zinc-200 rounded-lg p-8 text-center text-xs text-zinc-400">
                No hay convocatorias activas para el territorio seleccionado.
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
