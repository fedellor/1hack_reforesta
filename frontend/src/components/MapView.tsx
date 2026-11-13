'use client';

import React, { useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { MapPin, Euro, Sparkles, ChevronRight, Layers, Compass, CheckCircle2 } from 'lucide-react';

interface MapViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

interface CCAAData {
  id: string;
  nombre: string;
  codigo: string;
  cx: number;
  cy: number;
  r: number;
}

export function MapView({ convocatorias, onSeleccionar }: MapViewProps) {
  const [regionSeleccionada, setRegionSeleccionada] = useState<string>('todos');

  // Coordenadas aproximadas para nodos territoriales interactivos de España
  const ccaaNodes: CCAAData[] = [
    { id: 'Galicia', nombre: 'Galicia', codigo: 'GA', cx: 120, cy: 90, r: 24 },
    { id: 'Asturias', nombre: 'Asturias', codigo: 'AS', cx: 200, cy: 75, r: 18 },
    { id: 'Cantabria', nombre: 'Cantabria', codigo: 'CB', cx: 270, cy: 75, r: 16 },
    { id: 'País Vasco', nombre: 'País Vasco', codigo: 'PV', cx: 330, cy: 80, r: 18 },
    { id: 'Navarra', nombre: 'Navarra', codigo: 'NC', cx: 380, cy: 100, r: 18 },
    { id: 'Aragón', nombre: 'Aragón', codigo: 'AR', cx: 400, cy: 160, r: 26 },
    { id: 'Cataluña', nombre: 'Cataluña', codigo: 'CT', cx: 480, cy: 140, r: 26 },
    { id: 'Castilla y León', nombre: 'Castilla y León', codigo: 'CL', cx: 230, cy: 155, r: 34 },
    { id: 'Comunidad de Madrid', nombre: 'Madrid', codigo: 'MD', cx: 275, cy: 220, r: 22 },
    { id: 'La Rioja', nombre: 'La Rioja', codigo: 'RI', cx: 320, cy: 115, r: 15 },
    { id: 'Extremadura', nombre: 'Extremadura', codigo: 'EX', cx: 170, cy: 270, r: 26 },
    { id: 'Castilla-La Mancha', nombre: 'Castilla-La Mancha', codigo: 'CM', cx: 310, cy: 270, r: 32 },
    { id: 'Comunidad Valenciana', nombre: 'C. Valenciana', codigo: 'VC', cx: 410, cy: 260, r: 24 },
    { id: 'Región de Murcia', nombre: 'Murcia', codigo: 'MU', cx: 390, cy: 330, r: 18 },
    { id: 'Andalucía', nombre: 'Andalucía', codigo: 'AN', cx: 240, cy: 360, r: 36 },
    { id: 'Islas Baleares', nombre: 'Baleares', codigo: 'IB', cx: 520, cy: 250, r: 18 },
    { id: 'Canarias', nombre: 'Canarias', codigo: 'CN', cx: 100, cy: 440, r: 20 },
  ];

  // Helper para contar convocatorias y euros por territorio
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

  // Convocatorias a mostrar según selección
  const convocatoriasFiltradas = convocatorias.filter((c) => {
    if (regionSeleccionada === 'todos') return true;
    if (regionSeleccionada === 'Estatal') return c.ambitoTerritorial.toLowerCase().includes('estatal');
    return c.ambitoTerritorial.toLowerCase().includes(regionSeleccionada.toLowerCase());
  });

  const totalEurosSeleccion = convocatoriasFiltradas.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);

  return (
    <div className="space-y-6">
      
      {/* Barra de Filtro Rápido Territorial */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="h-5 w-5 text-emerald-600" />
            <h2 className="text-base font-bold text-slate-900">Radar Territorial de Financiación</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Explora las convocatorias públicas y privadas según la ubicación geográfica de los proyectos y convenios de custodia.
          </p>
        </div>

        {/* Botones de Selección Rápida */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <button
            onClick={() => setRegionSeleccionada('todos')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
              regionSeleccionada === 'todos'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            🌍 Todo el Territorio ({convocatorias.length})
          </button>

          <button
            onClick={() => setRegionSeleccionada('Estatal')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 ${
              regionSeleccionada === 'Estatal'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100'
            }`}
          >
            <span>🇪🇸 Ámbito Estatal / MITECO</span>
            <span className="font-mono bg-white/30 px-1.5 py-0.2 rounded text-[10px]">
              {statsEstatal.count}
            </span>
          </button>
        </div>
      </div>

      {/* Grid Principal: Mapa Visual Interactivo + Lista Lateral */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Mapa Interactivo (SVG) */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-emerald-600" />
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">
                Mapa Interactivo de Comunidades Autónomas
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">Haz clic en una región para filtrar</span>
          </div>

          {/* SVG Map Container */}
          <div className="relative bg-slate-900/95 rounded-xl p-4 border border-slate-800 flex items-center justify-center overflow-hidden">
            
            {/* Fondo de rejilla decorativa */}
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:16px_16px]" />

            <svg viewBox="50 40 520 420" className="w-full max-h-[420px] select-none">
              
              {/* Conexiones sutiles entre nodos */}
              <g stroke="#334155" strokeWidth="1" strokeDasharray="3,3" opacity="0.4">
                <line x1="120" y1="90" x2="230" y2="155" />
                <line x1="200" y1="75" x2="230" y2="155" />
                <line x1="230" y1="155" x2="275" y2="220" />
                <line x1="275" y1="220" x2="310" y2="270" />
                <line x1="310" y1="270" x2="240" y2="360" />
                <line x1="275" y1="220" x2="400" y2="160" />
                <line x1="400" y1="160" x2="480" y2="140" />
                <line x1="310" y1="270" x2="410" y2="260" />
              </g>

              {/* Nodos de Comunidades Autónomas */}
              {ccaaNodes.map((nodo) => {
                const stats = getStatsRegion(nodo.id);
                const tieneFondos = stats.count > 0;
                const estaSeleccionada = regionSeleccionada.toLowerCase().includes(nodo.id.toLowerCase());

                return (
                  <g
                    key={nodo.id}
                    onClick={() => setRegionSeleccionada(nodo.id)}
                    className="cursor-pointer transition-all duration-300 group"
                  >
                    {/* Anillo de pulso si tiene fondos activos */}
                    {tieneFondos && (
                      <circle
                        cx={nodo.cx}
                        cy={nodo.cy}
                        r={nodo.r + 5}
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="1.5"
                        strokeOpacity="0.4"
                        className="animate-pulse"
                      />
                    )}

                    {/* Círculo base de la región */}
                    <circle
                      cx={nodo.cx}
                      cy={nodo.cy}
                      r={nodo.r}
                      fill={
                        estaSeleccionada
                          ? '#059669' // Emerald activo
                          : tieneFondos
                          ? '#064e3b' // Verde oscuro con fondos
                          : '#1e293b' // Slate inactivo
                      }
                      stroke={estaSeleccionada ? '#34d399' : tieneFondos ? '#10b981' : '#475569'}
                      strokeWidth={estaSeleccionada ? 3 : tieneFondos ? 2 : 1}
                      className="group-hover:fill-emerald-600 transition-colors"
                    />

                    {/* Texto: Código de la CCAA */}
                    <text
                      x={nodo.cx}
                      y={nodo.cy - (tieneFondos ? 2 : 0)}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#ffffff"
                      fontSize={nodo.r > 20 ? '11' : '9'}
                      fontWeight="bold"
                      className="pointer-events-none"
                    >
                      {nodo.codigo}
                    </text>

                    {/* Badge con número de convocatorias si > 0 */}
                    {tieneFondos && (
                      <g>
                        <circle
                          cx={nodo.cx + nodo.r - 4}
                          cy={nodo.cy - nodo.r + 4}
                          r="8"
                          fill="#10b981"
                          stroke="#064e3b"
                          strokeWidth="1.5"
                        />
                        <text
                          x={nodo.cx + nodo.r - 4}
                          y={nodo.cy - nodo.r + 5}
                          textAnchor="middle"
                          dominantBaseline="middle"
                          fill="#ffffff"
                          fontSize="9"
                          fontWeight="black"
                        >
                          {stats.count}
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Leyenda del Mapa */}
            <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-xs border border-slate-800 rounded-lg p-2 text-[10px] text-slate-300 space-y-1">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50" />
                <span>Convocatorias Autonómicas Activas</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
                <span>Sin convocatorias específicas</span>
              </div>
            </div>

          </div>

          {/* Información de Ámbito Estatal */}
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-base">🇪🇸</span>
              <div>
                <p className="font-bold text-emerald-950">Convocatorias Estatales (MITECO)</p>
                <p className="text-[11px] text-emerald-800">
                  Aplicables a proyectos en cualquier Comunidad Autónoma
                </p>
              </div>
            </div>
            <button
              onClick={() => setRegionSeleccionada('Estatal')}
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-xs transition-colors"
            >
              Ver {statsEstatal.count} Estatales
            </button>
          </div>

        </div>

        {/* Lista Lateral de Oportunidades del Territorio Seleccionado */}
        <div className="lg:col-span-5 space-y-3">
          
          {/* Header del Panel Lateral */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 mb-2.5">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400">Territorio Seleccionado</span>
                <h3 className="font-black text-sm text-slate-900 flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-emerald-600" />
                  {regionSeleccionada === 'todos' ? 'Todo el Territorio' : regionSeleccionada}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-bold text-slate-400">Total Disponible</span>
                <p className="text-sm font-black text-emerald-700">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    totalEurosSeleccion
                  )}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600">
              {convocatoriasFiltradas.length}{' '}
              {convocatoriasFiltradas.length === 1 ? 'oportunidad encontrada' : 'oportunidades encontradas'}
            </p>
          </div>

          {/* Tarjetas de Convocatoria en la Región */}
          <div className="space-y-2.5 max-h-[480px] overflow-y-auto pr-1">
            {convocatoriasFiltradas.map((c) => (
              <div
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="bg-white border border-slate-200 rounded-xl p-3.5 hover:border-emerald-400 hover:shadow-xs transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-[10px] font-bold text-slate-500">{c.codigoOficial}</span>
                  <span className="bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.2 rounded text-[10px]">
                    {c.matchingGlobal}% Match
                  </span>
                </div>

                <h4 className="font-bold text-xs text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-2">
                  {c.titulo}
                </h4>

                <p className="text-[11px] text-slate-500 mt-0.5 truncate">{c.organismo}</p>

                <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100 text-xs">
                  <span className="font-black text-slate-900">
                    {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                      c.cuantiaMaximaProyecto
                    )}
                  </span>
                  <span className="text-[11px] font-semibold text-emerald-700 flex items-center gap-0.5">
                    Ficha ejecutiva <ChevronRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white border border-dashed border-slate-300 rounded-xl p-8 text-center text-xs text-slate-400">
                No hay convocatorias activas para este territorio. Selecciona otra región o haz clic en &ldquo;Todo el Territorio&rdquo;.
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
