'use client';

import React, { useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { MapPin, ChevronRight, Compass } from 'lucide-react';

interface MapViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

interface RegionGeo {
  id: string;
  nombre: string;
  d: string; // SVG path data
  labelX: number;
  labelY: number;
}

export function MapView({ convocatorias, onSeleccionar }: MapViewProps) {
  const [regionSeleccionada, setRegionSeleccionada] = useState<string>('todos');

  // Trazados vectoriales de silueta aproximada para las CCAA de España (Península e Islas)
  const regiones: RegionGeo[] = [
    {
      id: 'Galicia',
      nombre: 'Galicia',
      d: 'M 40,75 L 85,60 L 105,75 L 100,120 L 70,135 L 45,130 L 35,95 Z',
      labelX: 70,
      labelY: 95,
    },
    {
      id: 'Asturias',
      nombre: 'Asturias',
      d: 'M 105,75 L 165,70 L 165,95 L 105,100 Z',
      labelX: 135,
      labelY: 85,
    },
    {
      id: 'Cantabria',
      nombre: 'Cantabria',
      d: 'M 165,70 L 210,70 L 205,95 L 165,95 Z',
      labelX: 185,
      labelY: 83,
    },
    {
      id: 'País Vasco',
      nombre: 'País Vasco',
      d: 'M 210,70 L 250,75 L 245,105 L 205,95 Z',
      labelX: 228,
      labelY: 85,
    },
    {
      id: 'Navarra',
      nombre: 'Navarra',
      d: 'M 250,75 L 290,90 L 270,125 L 245,105 Z',
      labelX: 265,
      labelY: 100,
    },
    {
      id: 'La Rioja',
      nombre: 'La Rioja',
      d: 'M 220,100 L 255,108 L 245,125 L 215,115 Z',
      labelX: 235,
      labelY: 115,
    },
    {
      id: 'Aragón',
      nombre: 'Aragón',
      d: 'M 290,90 L 340,110 L 335,175 L 305,210 L 270,165 L 270,125 Z',
      labelX: 305,
      labelY: 150,
    },
    {
      id: 'Cataluña',
      nombre: 'Cataluña',
      d: 'M 340,110 L 415,115 L 400,170 L 350,185 L 335,175 Z',
      labelX: 375,
      labelY: 145,
    },
    {
      id: 'Castilla y León',
      nombre: 'Castilla y León',
      d: 'M 100,120 L 165,95 L 220,100 L 245,125 L 270,165 L 240,205 L 200,210 L 150,215 L 120,175 L 100,160 Z',
      labelX: 180,
      labelY: 155,
    },
    {
      id: 'Comunidad de Madrid',
      nombre: 'Madrid',
      d: 'M 225,200 L 255,195 L 260,225 L 230,230 Z',
      labelX: 242,
      labelY: 213,
    },
    {
      id: 'Extremadura',
      nombre: 'Extremadura',
      d: 'M 115,215 L 180,215 L 185,290 L 130,295 L 110,250 Z',
      labelX: 145,
      labelY: 255,
    },
    {
      id: 'Castilla-La Mancha',
      nombre: 'Castilla-La Mancha',
      d: 'M 200,210 L 240,205 L 270,200 L 305,210 L 320,270 L 275,305 L 210,300 L 185,290 L 180,215 L 225,200 L 230,230 L 260,225 L 255,195 Z',
      labelX: 250,
      labelY: 260,
    },
    {
      id: 'Comunidad Valenciana',
      nombre: 'C. Valenciana',
      d: 'M 335,175 L 350,185 L 340,250 L 320,295 L 305,280 L 320,270 L 305,210 Z',
      labelX: 330,
      labelY: 235,
    },
    {
      id: 'Región de Murcia',
      nombre: 'Murcia',
      d: 'M 295,290 L 325,295 L 315,330 L 280,325 Z',
      labelX: 302,
      labelY: 310,
    },
    {
      id: 'Andalucía',
      nombre: 'Andalucía',
      d: 'M 110,295 L 185,290 L 210,300 L 275,305 L 315,330 L 290,365 L 205,375 L 150,365 L 105,335 Z',
      labelX: 205,
      labelY: 335,
    },
    {
      id: 'Islas Baleares',
      nombre: 'Baleares',
      d: 'M 410,210 L 440,205 L 435,225 L 405,230 Z M 435,235 L 450,235 L 445,245 Z',
      labelX: 425,
      labelY: 218,
    },
    {
      id: 'Canarias',
      nombre: 'Canarias',
      d: 'M 50,380 L 120,380 L 120,410 L 50,410 Z',
      labelX: 85,
      labelY: 395,
    },
  ];

  // Helper de estadísticas por territorio
  const getStatsRegion = (nombreRegion: string) => {
    const list = convocatorias.filter((c) =>
      c.ambitoTerritorial.toLowerCase().includes(nombreRegion.toLowerCase())
    );
    const totalEuros = list.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);
    return {
      count: list.length,
      euros: totalEuros,
    };
  };

  const statsEstatal = getStatsRegion('Estatal');

  // Filtrar según región elegida
  const convocatoriasFiltradas = convocatorias.filter((c) => {
    if (regionSeleccionada === 'todos') return true;
    if (regionSeleccionada === 'Estatal') return c.ambitoTerritorial.toLowerCase().includes('estatal');
    return c.ambitoTerritorial.toLowerCase().includes(regionSeleccionada.toLowerCase());
  });

  const totalEurosSeleccion = convocatoriasFiltradas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);

  return (
    <div className="space-y-4">
      
      {/* Selector de Ámbito */}
      <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-emerald-700" />
          <span className="font-bold text-slate-800">Distribución Territorial de Fondos</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setRegionSeleccionada('todos')}
            className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors ${
              regionSeleccionada === 'todos'
                ? 'bg-slate-900 text-white font-semibold'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
          >
            Todo el Territorio ({convocatorias.length})
          </button>

          <button
            onClick={() => setRegionSeleccionada('Estatal')}
            className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors ${
              regionSeleccionada === 'Estatal'
                ? 'bg-emerald-700 text-white font-semibold'
                : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            Ámbito Estatal / MITECO ({statsEstatal.count})
          </button>
        </div>
      </div>

      {/* Grid: Mapa SVG Geográfico + Convocatorias */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        {/* Mapa SVG Geográfico de España */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-lg p-4 shadow-2xs">
          <div className="flex items-center justify-between mb-2 text-xs">
            <span className="font-semibold text-slate-700">Comunidades Autónomas</span>
            <span className="text-slate-400 text-[11px]">Haz clic en una comunidad para filtrar</span>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-2 flex items-center justify-center">
            <svg viewBox="30 50 430 370" className="w-full max-h-[380px] select-none">
              
              {/* Rutas de las Comunidades Autónomas */}
              {regiones.map((r) => {
                const stats = getStatsRegion(r.id);
                const tieneFondos = stats.count > 0;
                const estaSeleccionada = regionSeleccionada.toLowerCase().includes(r.id.toLowerCase());

                return (
                  <g
                    key={r.id}
                    onClick={() => setRegionSeleccionada(r.id)}
                    className="cursor-pointer group transition-all"
                  >
                    {/* Polígono de la CCAA */}
                    <path
                      d={r.d}
                      fill={
                        estaSeleccionada
                          ? '#047857' // Emerald-700 activo
                          : tieneFondos
                          ? '#10b981' // Emerald-500 con fondos
                          : '#cbd5e1' // Slate-300 sin fondos
                      }
                      stroke="#ffffff"
                      strokeWidth="1.5"
                      strokeLinejoin="round"
                      className="group-hover:opacity-85 transition-opacity"
                    />

                    {/* Etiqueta de Texto */}
                    <text
                      x={r.labelX}
                      y={r.labelY}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill={tieneFondos || estaSeleccionada ? '#ffffff' : '#475569'}
                      fontSize="9"
                      fontWeight="600"
                      className="pointer-events-none"
                    >
                      {r.nombre}
                    </text>

                    {/* Contador si tiene convocatorias */}
                    {tieneFondos && (
                      <circle
                        cx={r.labelX + 16}
                        cy={r.labelY - 7}
                        r="5.5"
                        fill="#065f46"
                        stroke="#ffffff"
                        strokeWidth="1"
                      />
                    )}
                    {tieneFondos && (
                      <text
                        x={r.labelX + 16}
                        y={r.labelY - 6.5}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#ffffff"
                        fontSize="7"
                        fontWeight="bold"
                        className="pointer-events-none"
                      >
                        {stats.count}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Recuadro de Canarias */}
              <text x="85" y="372" textAnchor="middle" fontSize="8" fill="#64748b" fontWeight="bold">
                Islas Canarias
              </text>
              <rect x="40" y="360" width="90" height="55" fill="none" stroke="#cbd5e1" strokeDasharray="2,2" />

            </svg>
          </div>

          {/* Leyenda sobria */}
          <div className="flex items-center justify-between mt-3 text-[11px] text-slate-500 pt-2 border-t border-slate-100">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500" />
                <span>Convocatorias Autonómicas</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-sm bg-slate-300" />
                <span>Sin convocatorias activas</span>
              </span>
            </div>

            <button
              onClick={() => setRegionSeleccionada('Estatal')}
              className="text-emerald-700 font-semibold hover:underline"
            >
              Ver {statsEstatal.count} de ámbito estatal
            </button>
          </div>
        </div>

        {/* Panel Lateral de Convocatorias en el Territorio */}
        <div className="lg:col-span-5 space-y-3">
          
          <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-2xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
              <div>
                <span className="text-[10px] uppercase font-semibold text-slate-400">Territorio</span>
                <h3 className="font-bold text-sm text-slate-900 flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-emerald-700" />
                  {regionSeleccionada === 'todos' ? 'Todo el Territorio' : regionSeleccionada}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Total Disponible</span>
                <p className="text-sm font-extrabold text-slate-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    totalEurosSeleccion
                  )}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-500">
              {convocatoriasFiltradas.length}{' '}
              {convocatoriasFiltradas.length === 1 ? 'oportunidad' : 'oportunidades'}
            </p>
          </div>

          <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
            {convocatoriasFiltradas.map((c) => (
              <div
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="bg-white border border-slate-200 rounded-lg p-3 hover:border-slate-400 transition-colors cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-[10px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded">
                    {c.codigoOficial}
                  </span>
                  <span className="text-emerald-800 bg-emerald-50 font-bold px-1.5 py-0.2 rounded text-[10px]">
                    {c.matchingGlobal}% Match
                  </span>
                </div>

                <h4 className="font-bold text-xs text-slate-900 line-clamp-2">
                  {c.titulo}
                </h4>

                <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-xs">
                  <span className="font-bold text-slate-900">
                    {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                      c.cuantiaMaximaProyecto
                    )}
                  </span>
                  <span className="text-[11px] font-medium text-emerald-700 flex items-center gap-0.5">
                    Ver ficha <ChevronRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white border border-dashed border-slate-200 rounded-lg p-6 text-center text-xs text-slate-400">
                No hay convocatorias activas para este territorio.
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
