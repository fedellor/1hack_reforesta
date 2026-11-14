'use client';

import React from 'react';
import { Building2, ExternalLink, Repeat } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { diasHastaApertura, esProxima, plazoSinFijar } from '@/lib/plazo';
import { esCitaLiteral, limpiarJustificacion } from '@/lib/texto';
import { Programa, nombreMes, recurrenciaDe } from '@/lib/recurrencia';

interface EmpresasViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (c: Convocatoria) => void;
  /** Programas recurrentes detectados en el histórico (vacío si aún no hay histórico) */
  programas?: Programa[];
}

/**
 * Canal de mecenazgo (empresas y fundaciones). Cada tarjeta responde a lo que el equipo necesita para decidir si llamar:
 * por qué encaja, qué cubre, cuánto aportan, cuándo, si se repite cada año y cómo acceder a las bases.
 */
export function EmpresasView({ convocatorias, onSeleccionar, programas = [] }: EmpresasViewProps) {
  if (convocatorias.length === 0) {
    return <p className="py-16 text-center text-zinc-400">No hay programas de empresas con los filtros actuales.</p>;
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      {convocatorias.map((c) => {
        const literal = c.citasBasesJustificacion.find(esCitaLiteral);
        const porQue = literal ?? (c.citasBasesJustificacion[0] ? limpiarJustificacion(c.citasBasesJustificacion[0]) : c.motivoElegibilidad);
        const rec = recurrenciaDe(c, programas);
        return (
          <article key={c.id} className="flex flex-col border-t-4 border-brand bg-zinc-50 p-5">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500">
              <Building2 className="h-4 w-4 text-brand" /> {c.organismo}
            </p>
            <h3 className="mt-2 font-serif text-lg font-bold leading-snug text-zinc-900 line-clamp-3">{c.titulo}</h3>

            {porQue && (
              <p className={`mt-3 border-l-2 border-brand pl-3 text-sm text-zinc-600 line-clamp-3 ${literal ? 'italic' : ''}`}>
                <span className="block not-italic text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Por qué encaja</span>
                {literal ? `“${porQue}”` : porQue}
              </p>
            )}
            <p className="mt-3 text-sm text-zinc-700">
              <strong>Cubre:</strong> {c.accionesSubvencionables.slice(0, 2).join(' · ') || 'Ver ficha'}
            </p>

            <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
              <span className="rounded-full bg-brand px-3 py-1 text-white">Encaje {c.matchingGlobal}%</span>
              <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">
                {esProxima(c) ? `Abre en ${diasHastaApertura(c)} d` : plazoSinFijar(c) ? 'Plazo abierto' : `Cierra en ${c.diasRestantes} d`}
              </span>
              <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">
                {c.porcentajeCofinanciacion === 0 ? 'Sin cofinanciación' : `Aportas ${c.porcentajeCofinanciacion}%`}
              </span>
              {rec && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-amber-800" title={`Ediciones: ${rec.anios.join(', ')}`}>
                  <Repeat className="h-3 w-3" /> Se repite · suele salir en {nombreMes(rec.mesApertura)}
                </span>
              )}
            </div>

            <div className="mt-auto pt-5 flex items-end justify-between gap-4">
              <div>
                <span className="block text-xs uppercase tracking-wide text-zinc-500">Aportación máxima</span>
                <span className="font-serif text-2xl font-bold text-zinc-900">{formatoEuros(c.cuantiaMaximaProyecto)}</span>
              </div>
              <div className="flex flex-col items-end gap-1.5 text-xs font-semibold">
                {c.urlSedeElectronica && (
                  <a href={c.urlSedeElectronica} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-emerald-800 hover:underline">
                    Solicitar <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {c.urlBasesPdf && (
                  <a href={c.urlBasesPdf} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-zinc-600 hover:underline">
                    Bases <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                <button onClick={() => onSeleccionar(c)} className="rounded-full bg-white border border-zinc-300 px-5 py-2 uppercase tracking-wide text-zinc-900 hover:bg-zinc-900 hover:text-white transition-colors">
                  Ver ficha
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
