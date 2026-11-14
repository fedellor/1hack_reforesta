'use client';

import React from 'react';
import { Building2, ExternalLink, Repeat } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { diasHastaApertura, esProxima, plazoSinFijar } from '@/lib/plazo';
import { esCitaLiteral, limpiarJustificacion } from '@/lib/texto';
import { Programa, recurrenciaDe, textoVentana } from '@/lib/recurrencia';

interface EmpresasViewProps {
  convocatorias: Convocatoria[];
  cerradas?: Convocatoria[];
  onSeleccionar: (c: Convocatoria) => void;
  /** Programas recurrentes detectados en el histórico (vacío si aún no hay histórico) */
  programas?: Programa[];
  soloElegibles?: boolean;
  onToggleSoloElegibles?: () => void;
}

/**
 * Canal de mecenazgo (empresas y fundaciones). Cada tarjeta responde a lo que el equipo necesita para decidir si llamar:
 * por qué encaja, qué cubre, cuánto aportan, cuándo, si se repite cada año y cómo acceder a las bases.
 */
export function EmpresasView({
  convocatorias,
  cerradas = [],
  onSeleccionar,
  programas = [],
  soloElegibles = true,
  onToggleSoloElegibles,
}: EmpresasViewProps) {
  const renderTarjeta = (c: Convocatoria, esHistorica = false) => {
    const literal = c.citasBasesJustificacion.find(esCitaLiteral);
    const porQue = !c.elegible
      ? (c.dealbreakers[0] ?? c.motivoElegibilidad)
      : (literal ?? (c.citasBasesJustificacion[0] ? limpiarJustificacion(c.citasBasesJustificacion[0]) : c.motivoElegibilidad));
    const rec = recurrenciaDe(c, programas);
    return (
      <article key={c.id} className={`flex flex-col border-t-4 p-5 ${c.elegible ? 'border-brand bg-zinc-50' : 'border-rose-500 bg-rose-50/40'}`}>
        <div className="flex items-center justify-between gap-2">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-zinc-500 min-w-0 truncate">
            <Building2 className={`h-4 w-4 shrink-0 ${c.elegible ? 'text-brand' : 'text-rose-600'}`} /> {c.organismo}
          </p>
          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${c.elegible ? 'bg-emerald-100 text-emerald-900' : 'bg-rose-600 text-white'}`}>
            {c.elegible ? 'Apta Reforesta' : 'Excluida'}
          </span>
        </div>
        <h3 className="mt-2 font-serif text-lg font-bold leading-snug text-zinc-900 line-clamp-3">{c.titulo}</h3>

        {porQue && (
          <p className={`mt-3 border-l-2 pl-3 text-sm line-clamp-3 ${c.elegible ? `border-brand text-zinc-600 ${literal ? 'italic' : ''}` : 'border-rose-400 text-rose-800'}`}>
            <span className="block not-italic text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              {c.elegible ? 'Por qué encaja' : 'Motivo de exclusión'}
            </span>
            {c.elegible && literal ? `“${porQue}”` : porQue}
          </p>
        )}
        <p className="mt-3 text-sm text-zinc-700">
          <strong>Cubre:</strong> {c.accionesSubvencionables.slice(0, 2).join(' · ') || 'Ver ficha'}
        </p>

        <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
          <span className="rounded-full bg-brand px-3 py-1 text-white">Encaje {c.matchingGlobal}%</span>
          <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">
            {esHistorica
              ? `Cerrada (${c.anio ?? c.fechaCierre.slice(0, 4)})`
              : esProxima(c)
                ? `Abre en ${diasHastaApertura(c)} d`
                : plazoSinFijar(c)
                  ? 'Plazo abierto'
                  : `Cierra en ${c.diasRestantes} d`}
          </span>
          <span className="rounded-full border border-zinc-300 px-3 py-1 text-zinc-700">
            {c.porcentajeCofinanciacion === 0 ? 'Sin cofinanciación' : `Aportas ${c.porcentajeCofinanciacion}%`}
          </span>
          {rec && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-amber-800" title={`Ediciones: ${rec.anios.join(', ')}`}>
              <Repeat className="h-3 w-3" /> Se repite · suele salir en {textoVentana(rec)}
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
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 pb-3 text-xs">
        <p className="text-zinc-600">
          <strong className="text-zinc-900">{convocatorias.length}</strong> activas ·{' '}
          <strong className="text-zinc-900">{cerradas.length}</strong> ediciones históricas de fundaciones y empresas
        </p>
        {onToggleSoloElegibles && (
          <button
            type="button"
            onClick={onToggleSoloElegibles}
            className={`px-4 py-2 rounded-full border font-semibold uppercase tracking-wide transition-colors ${
              soloElegibles ? 'bg-brand border-brand text-white' : 'bg-white border-zinc-200 text-zinc-700 hover:bg-zinc-50'
            }`}
          >
            {soloElegibles ? 'Solo aptas Reforesta' : 'Todas (incl. excluidas)'}
          </button>
        )}
      </div>

      {convocatorias.length === 0 && cerradas.length === 0 ? (
        <p className="py-16 text-center text-zinc-400">No hay programas de empresas con los filtros actuales.</p>
      ) : (
        <>
          {convocatorias.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {convocatorias.map((c) => renderTarjeta(c, false))}
            </div>
          )}
          {cerradas.length > 0 && (
            <section className="space-y-3 pt-4 border-t border-zinc-200">
              <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">
                Ediciones anteriores / referencia histórica RSC ({cerradas.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                {cerradas.map((c) => renderTarjeta(c, true))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
