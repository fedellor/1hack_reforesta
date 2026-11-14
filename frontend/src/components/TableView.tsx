'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { ChevronRight } from 'lucide-react';

interface TableViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

export function TableView({ convocatorias, onSeleccionar }: TableViewProps) {
  return (
    <div className="bg-white rounded-lg border border-zinc-200 overflow-hidden shadow-2xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-zinc-50 border-b border-zinc-200 text-zinc-500 font-medium uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-2.5 px-3">Código</th>
              <th className="py-2.5 px-3">Convocatoria & Organismo</th>
              <th className="py-2.5 px-3">Ámbito</th>
              <th className="py-2.5 px-3 text-right">Cuantía Máx</th>
              <th className="py-2.5 px-3">Cofinanc.</th>
              <th className="py-2.5 px-3">Cierre</th>
              <th className="py-2.5 px-3">Elegibilidad</th>
              <th className="py-2.5 px-3 text-right">Encaje</th>
              <th className="py-2.5 px-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {convocatorias.map((c) => (
              <tr
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="hover:bg-zinc-50 transition-colors cursor-pointer group"
              >
                {/* Código */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <span className="font-mono text-[11px] font-semibold text-zinc-700">
                    {c.codigoOficial}
                  </span>
                </td>

                {/* Título & Organismo */}
                <td className="py-3 px-3">
                  <p className="font-semibold text-zinc-900 group-hover:text-emerald-800 transition-colors line-clamp-1 max-w-md">
                    {c.titulo}
                  </p>
                  <p className="text-[11px] text-zinc-500 truncate max-w-sm mt-0.5">
                    {c.organismo}
                  </p>
                </td>

                {/* Ámbito */}
                <td className="py-3 px-3 whitespace-nowrap text-zinc-600 font-medium">
                  {c.ambitoTerritorial}
                </td>

                {/* Cuantía */}
                <td className="py-3 px-3 whitespace-nowrap text-right font-mono font-bold text-zinc-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </td>

                {/* Cofinanciación */}
                <td className="py-3 px-3 whitespace-nowrap text-zinc-600 font-medium">
                  {c.porcentajeCofinanciacion === 0 ? (
                    <span className="text-zinc-700">100%</span>
                  ) : (
                    <span className="text-amber-800">{100 - c.porcentajeCofinanciacion}%</span>
                  )}
                </td>

                {/* Cierre */}
                <td className="py-3 px-3 whitespace-nowrap font-medium">
                  <span
                    className={
                      c.diasRestantes <= 7
                        ? 'text-rose-700 font-semibold'
                        : c.diasRestantes <= 20
                        ? 'text-amber-800'
                        : 'text-zinc-600'
                    }
                  >
                    {c.diasRestantes}d
                  </span>
                </td>

                {/* Elegibilidad */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <div className="flex items-center gap-1.5 font-medium text-xs">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        c.elegible ? 'bg-emerald-600' : 'bg-rose-600'
                      }`}
                    />
                    <span className={c.elegible ? 'text-zinc-800' : 'text-rose-700'}>
                      {c.elegible ? 'Apta' : 'Excluida'}
                    </span>
                  </div>
                </td>

                {/* Encaje */}
                <td className="py-3 px-3 whitespace-nowrap text-right font-mono font-bold">
                  <span
                    className={
                      c.matchingGlobal >= 90
                        ? 'text-emerald-800'
                        : c.matchingGlobal >= 80
                        ? 'text-zinc-800'
                        : 'text-zinc-400'
                    }
                  >
                    {c.matchingGlobal}%
                  </span>
                </td>

                {/* Flecha */}
                <td className="py-3 px-2 whitespace-nowrap text-right text-zinc-400 group-hover:text-zinc-700">
                  <ChevronRight className="h-3.5 w-3.5" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
