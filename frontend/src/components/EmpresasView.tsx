'use client';

import React from 'react';
import { Building2 } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { plazoSinFijar } from '@/lib/plazo';

/** Sección «¿Quién financia?»: programas corporativos y fundaciones, en tarjetas centradas en la entidad. */
export function EmpresasView({ convocatorias, onSeleccionar }: { convocatorias: Convocatoria[]; onSeleccionar: (c: Convocatoria) => void }) {
  if (convocatorias.length === 0) {
    return <p className="py-16 text-center text-zinc-400">No hay programas de empresas con los filtros actuales.</p>;
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      {convocatorias.map((c) => (
        <article key={c.id} className="flex flex-col border-t-4 border-brand bg-zinc-50 p-5">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
            <Building2 className="h-4 w-4 text-brand" /> {c.organismo}
          </p>
          <h3 className="mt-3 font-serif text-xl font-bold leading-snug text-zinc-900">{c.titulo}</h3>
          <p className="mt-3 text-sm text-zinc-600 line-clamp-2">{c.resumenEjecutivo}</p>
          <p className="mt-3 text-sm text-zinc-700">
            <strong>Cubre:</strong> {c.accionesSubvencionables.slice(0, 2).join(' · ') || 'Ver ficha'}
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold">
            <span className="rounded-full bg-brand px-3 py-1 text-white">Encaje {c.matchingGlobal}%</span>
            <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">{plazoSinFijar(c) ? 'Plazo abierto' : `Cierra en ${c.diasRestantes} d`}</span>
            <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">
              {c.porcentajeCofinanciacion === 0 ? 'Sin cofinanciación' : `Aportas ${c.porcentajeCofinanciacion}%`}
            </span>
          </div>
          <div className="mt-auto pt-6 flex items-end justify-between gap-4">
            <div>
              <span className="block text-xs uppercase tracking-wide text-zinc-500">Aportación máxima</span>
              <span className="font-serif text-2xl font-bold text-zinc-900">{formatoEuros(c.cuantiaMaximaProyecto)}</span>
            </div>
            <button
              onClick={() => onSeleccionar(c)}
              className="rounded-full bg-white border border-zinc-300 px-6 py-3 text-xs font-semibold uppercase tracking-wide text-zinc-900 hover:bg-zinc-900 hover:text-white transition-colors"
            >
              Ver más
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
