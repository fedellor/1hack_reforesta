'use client';

import React from 'react';
import { ChevronRight } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';

interface ConvocatoriaRowCardProps {
  convocatoria: Convocatoria;
  onSeleccionar: (convocatoria: Convocatoria) => void;
  seleccionada?: boolean;
}

const colorPlazo = (dias: number) =>
  dias < 7 ? 'border-rose-500 text-rose-700' : dias < 20 ? 'border-amber-500 text-amber-700' : 'border-brand text-emerald-700';

/**
 * Fila de decisión. Orden de lectura: ¿cuándo cierra? → ¿qué es y qué dice la base? → ¿cuánto dinero y a qué coste? → ¿encaja?
 */
export function ConvocatoriaRowCard({ convocatoria, onSeleccionar, seleccionada }: ConvocatoriaRowCardProps) {
  const c = convocatoria;
  const motivo = c.elegible ? c.citasBasesJustificacion[0] : c.dealbreakers[0] ?? c.motivoElegibilidad;
  const lineas: [string, number][] = [
    ['Restauración', c.matchingLineas.restauracionEcosistemas],
    ['Hábitats', c.matchingLineas.conservacionHabitats],
    ['Educación', c.matchingLineas.educacionAmbiental],
  ];

  return (
    <article
      onClick={() => onSeleccionar(c)}
      className={`group flex flex-col md:flex-row md:items-stretch gap-6 border bg-white p-6 cursor-pointer transition-colors ${
        seleccionada ? 'border-zinc-900' : 'border-zinc-200 hover:border-zinc-400'
      } ${!c.elegible ? 'bg-zinc-50 opacity-80' : ''}`}
    >
      {/* 1. Plazo o estado histórico */}
      <div
        className={`shrink-0 md:w-24 border-l-4 pl-4 ${
          c.estado === 'CERRADA'
            ? 'border-zinc-400 text-zinc-600'
            : c.estado === 'PROXIMA'
              ? 'border-[#1d70b8] text-[#1d70b8]'
              : colorPlazo(c.diasRestantes)
        }`}
      >
        {c.estado === 'CERRADA' ? (
          <>
            <span className="block font-serif text-3xl font-bold leading-none">
              {c.anio ?? String(c.fechaCierre).slice(0, 4)}
            </span>
            <span className="mt-0.5 block text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
              Cerrada
            </span>
            <span className="mt-1 block text-xs text-zinc-500">
              {new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}
            </span>
          </>
        ) : c.estado === 'PROXIMA' ? (
          <>
            <span className="block font-serif text-4xl font-bold leading-none">{c.diasRestantes}</span>
            <span className="block text-xs font-semibold uppercase tracking-wide">días · Próx.</span>
            <span className="mt-1 block text-xs text-zinc-500">
              {new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
            </span>
          </>
        ) : (
          <>
            <span className="block font-serif text-4xl font-bold leading-none">{c.diasRestantes}</span>
            <span className="block text-xs font-semibold uppercase tracking-wide">días</span>
            <span className="mt-1 block text-xs text-zinc-500">
              {new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
            </span>
          </>
        )}
      </div>

      {/* 2. Qué es y por qué encaja (o por qué no) */}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-zinc-500">
          {c.organismo}{c.organismo.includes(c.ambitoTerritorial) ? '' : ` · ${c.ambitoTerritorial}`}
        </p>
        <h3 className="mt-1 font-serif text-lg font-bold leading-snug text-zinc-900 group-hover:text-emerald-800 transition-colors line-clamp-2">
          {c.titulo}
        </h3>
        {motivo && (
          <p className={`mt-2 text-sm italic line-clamp-2 border-l-2 pl-3 ${c.elegible ? 'border-brand text-zinc-600' : 'border-rose-400 text-rose-700 not-italic font-medium'}`}>
            {c.elegible ? `“${motivo}”` : `Excluida: ${motivo}`}
          </p>
        )}
      </div>

      {/* 3. Dinero y coste real para la ONG */}
      <div className="shrink-0 md:w-44 md:text-right">
        <span className="block text-xl font-bold text-zinc-900">{formatoEuros(c.cuantiaMaximaProyecto)}</span>
        <span className="block text-sm text-zinc-600">
          {c.porcentajeCofinanciacion === 0 ? '100% financiado' : `Aportas ${c.porcentajeCofinanciacion}%`}
        </span>
        <span className="block text-xs text-zinc-500">Pago por {c.modalidadPago === 'mixto' ? 'anticipo y reembolso' : c.modalidadPago}</span>
      </div>

      {/* 4. Encaje y veredicto */}
      <div className="shrink-0 md:w-40">
        <div className="flex items-center gap-2 md:justify-end">
          <span
            className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ${
              c.elegible ? 'bg-brand text-white' : 'bg-rose-600 text-white'
            }`}
          >
            {c.elegible ? 'Apta' : 'Excluida'}
          </span>
          <span className="font-serif text-2xl font-bold text-zinc-900">{c.matchingGlobal}%</span>
        </div>
        <div className="mt-3 space-y-1">
          {lineas.map(([nombre, valor]) => (
            <div key={nombre} className="flex items-center gap-2 text-[11px] text-zinc-500">
              <span className="w-20 truncate">{nombre}</span>
              <span className="flex-1 h-1 bg-zinc-100">
                <span className="block h-full bg-brand" style={{ width: `${valor}%` }} />
              </span>
            </div>
          ))}
        </div>
      </div>

      <ChevronRight className="hidden md:block h-5 w-5 self-center text-zinc-300 group-hover:text-zinc-700 transition-colors shrink-0" />
    </article>
  );
}
