'use client';

import React from 'react';
import { Building2 } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';

/** Sección «¿Quién financia?»: programas corporativos y fundaciones, en tarjetas centradas en la entidad. */
export function EmpresasView({ convocatorias, onSeleccionar }: { convocatorias: Convocatoria[]; onSeleccionar: (c: Convocatoria) => void }) {
  return (
    <div className="space-y-6">
      <div className="border border-[#6aa43a]/35 bg-[#eef5e6] p-5 rounded-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase tracking-wider text-[#2d5a27]">
              Incentivos Fiscales para Mecenazgo RSC · Asociación Declarada de Utilidad Pública (NIF G80428204)
            </p>
            <p className="text-sm text-zinc-700 leading-relaxed">
              De acuerdo con la certificación oficial de Utilidad Pública de Reforesta (Ley 49/2002), las empresas
              colaboradoras disfrutan de una <strong>deducción del 40% en el Impuesto sobre Sociedades</strong> (hasta el
              <strong> 50% a partir del 3.er año</strong> consecutivo, límite 15% de la base imponible), cumpliendo el
              <strong> Fin Estatutario 10</strong> (mejora ambiental y RSC corporativa).
            </p>
          </div>
          <a
            href="https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 rounded-sm bg-[#2d5a27] hover:bg-[#1e3d1a] text-white px-4 py-2 text-xs font-semibold uppercase tracking-wide transition-colors"
          >
            Certificado Utilidad Pública (PDF) ↗
          </a>
        </div>
      </div>

      {convocatorias.length === 0 ? (
        <div className="py-12 border border-dashed border-zinc-300 text-center space-y-2">
          <p className="text-zinc-600 font-medium">
            No hay convocatorias abiertas de fundaciones privadas en la ventana actual del radar.
          </p>
          <p className="text-xs text-zinc-400">
            El radar monitoriza en directo Fundación Biodiversidad, Iberdrola, La Caixa, Endesa, BBVA y Santander. Cuando abren nuevas convocatorias RSC de reforestación aparecen aquí automáticamente.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {convocatorias.map((c) => (
            <article key={c.id} className="flex flex-col border-t-4 border-brand bg-zinc-50 p-8">
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
                <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">Cierra en {c.diasRestantes} d</span>
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
      )}
    </div>
  );
}
