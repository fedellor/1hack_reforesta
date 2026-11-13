'use client';

import React, { useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { MapPin, Euro, Target, ChevronRight, Sparkles } from 'lucide-react';

interface MapViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function MapView({ convocatorias, onSeleccionar }: MapViewProps) {
  const [regionSeleccionada, setRegionSeleccionada] = useState<string>('Estatal');

  // Regiones principales de operación de Reforesta
  const regiones = [
    { id: 'Estatal', nombre: '🇪🇸 Todo el Estado / MITECO', desc: 'Fondos de cobertura nacional y fondos europeos centralizados' },
    { id: 'Comunidad de Madrid', nombre: '📍 Comunidad de Madrid', desc: 'Sierra de Guadarrama, cuencas del Jarama y Tajo' },
    { id: 'Galicia', nombre: '📍 Galicia', desc: 'Reforestación de montes vecinales y lucha contra incendios' },
    { id: 'Castilla y León', nombre: '📍 Castilla y León', desc: 'España vaciada, charcas y zonas riparias' },
  ];

  const convocatoriasRegion = convocatorias.filter((c) =>
    regionSeleccionada === 'todos' ? true : c.ambitoTerritorial.toLowerCase().includes(regionSeleccionada.toLowerCase())
  );

  const totalEurosRegion = convocatoriasRegion.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);

  return (
    <div className="space-y-6">
      
      {/* Selector de Regiones */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {regiones.map((r) => {
          const count = convocatorias.filter((c) =>
            c.ambitoTerritorial.toLowerCase().includes(r.id.toLowerCase())
          ).length;
          const esActiva = regionSeleccionada === r.id;

          return (
            <button
              key={r.id}
              onClick={() => setRegionSeleccionada(r.id)}
              className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                esActiva
                  ? 'bg-emerald-800 text-white border-emerald-900 shadow-md ring-2 ring-emerald-500/30'
                  : 'bg-white text-slate-800 border-slate-200 hover:border-emerald-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-xs">{r.nombre}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    esActiva ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {count} convocatorias
                </span>
              </div>
              <p className={`text-[11px] line-clamp-1 ${esActiva ? 'text-emerald-200' : 'text-slate-500'}`}>
                {r.desc}
              </p>
            </button>
          );
        })}
      </div>

      {/* Panel de Resultados de la Región Seleccionada */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="h-4 w-4 text-emerald-600" />
              Oportunidades en: <span className="text-emerald-700">{regionSeleccionada}</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Financiación disponible identificada para entidades de custodia del territorio y ONGs
            </p>
          </div>

          <div className="text-right">
            <span className="text-[10px] uppercase font-bold text-slate-400">Total Disponible</span>
            <p className="text-lg font-black text-emerald-700">
              {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                totalEurosRegion
              )}
            </p>
          </div>
        </div>

        {/* Lista de Convocatorias en la Región */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {convocatoriasRegion.map((c) => (
            <div
              key={c.id}
              onClick={() => onSeleccionar(c)}
              className="p-3.5 rounded-xl border border-slate-200 hover:border-emerald-400 hover:shadow-xs transition-all cursor-pointer bg-slate-50/50 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-mono text-[10px] font-semibold text-slate-500">{c.codigoOficial}</span>
                  <span className="bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded text-[10px]">
                    {c.matchingGlobal}% Match
                  </span>
                </div>
                <h4 className="font-bold text-xs text-slate-900 line-clamp-2">{c.titulo}</h4>
                <p className="text-[11px] text-slate-500 mt-1">{c.organismo}</p>
              </div>

              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-200/60 text-xs">
                <span className="font-black text-slate-800">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </span>
                <span className="text-[11px] font-medium text-emerald-700 flex items-center gap-1">
                  Ver ficha <ChevronRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          ))}

          {convocatoriasRegion.length === 0 && (
            <p className="text-xs text-slate-400 italic p-6 text-center col-span-2">
              No hay convocatorias activas registradas para este territorio en este momento.
            </p>
          )}
        </div>
      </div>

    </div>
  );
}
