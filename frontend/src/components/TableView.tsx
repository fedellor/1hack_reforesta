'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface TableViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function TableView({ convocatorias, onSeleccionar }: TableViewProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3 px-3">Match</th>
              <th className="py-3 px-3">Código & Organismo</th>
              <th className="py-3 px-4">Título Convocatoria</th>
              <th className="py-3 px-3">Ámbito</th>
              <th className="py-3 px-3 text-right">Cuantía Máx</th>
              <th className="py-3 px-3">Cofinanc.</th>
              <th className="py-3 px-3">Cierre</th>
              <th className="py-3 px-3">Elegibilidad</th>
              <th className="py-3 px-3 text-center">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {convocatorias.map((c) => (
              <tr
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="hover:bg-emerald-50/40 transition-colors cursor-pointer group"
              >
                {/* Match */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center font-bold px-2 py-0.5 rounded text-xs ${
                      c.matchingGlobal >= 90
                        ? 'bg-emerald-500 text-white'
                        : c.matchingGlobal >= 80
                        ? 'bg-emerald-100 text-emerald-900'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {c.matchingGlobal}%
                  </span>
                </td>

                {/* Código & Organismo */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <p className="font-mono font-semibold text-slate-900">{c.codigoOficial}</p>
                  <p className="text-[10px] text-slate-500 truncate max-w-[120px]">{c.organismo}</p>
                </td>

                {/* Título */}
                <td className="py-3 px-4">
                  <p className="font-semibold text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-1 max-w-md">
                    {c.titulo}
                  </p>
                  <p className="text-[10px] text-slate-500 truncate max-w-md italic mt-0.5">
                    {c.accionesSubvencionables.slice(0, 2).join(' · ')}
                  </p>
                </td>

                {/* Ámbito */}
                <td className="py-3 px-3 whitespace-nowrap text-slate-600 font-medium">
                  {c.ambitoTerritorial}
                </td>

                {/* Cuantía */}
                <td className="py-3 px-3 whitespace-nowrap text-right font-black text-slate-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </td>

                {/* Cofinanciación */}
                <td className="py-3 px-3 whitespace-nowrap font-medium">
                  {c.porcentajeCofinanciacion === 0 ? (
                    <span className="text-emerald-700">100% subv.</span>
                  ) : (
                    <span className="text-amber-700">{c.porcentajeCofinanciacion}% propio</span>
                  )}
                </td>

                {/* Cierre */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <span
                    className={`font-semibold ${
                      c.diasRestantes <= 7
                        ? 'text-rose-600'
                        : c.diasRestantes <= 20
                        ? 'text-amber-600'
                        : 'text-slate-600'
                    }`}
                  >
                    {c.diasRestantes}d ({new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })})
                  </span>
                </td>

                {/* Elegibilidad */}
                <td className="py-3 px-3 whitespace-nowrap">
                  {c.elegible ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" /> Apta
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-rose-700 font-medium">
                      <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> Excluida
                    </span>
                  )}
                </td>

                {/* Acción */}
                <td className="py-3 px-3 whitespace-nowrap text-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSeleccionar(c);
                    }}
                    className="px-2 py-1 rounded bg-slate-100 hover:bg-emerald-600 hover:text-white text-slate-700 font-semibold transition-colors text-[11px]"
                  >
                    Ficha
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
