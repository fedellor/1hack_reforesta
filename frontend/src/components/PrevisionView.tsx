'use client';

import React, { useMemo, useState } from 'react';
import { History } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { Programa, detectarProgramas, nombreMes } from '@/lib/recurrencia';
import { ProgramaDrawer } from '@/components/ProgramaDrawer';

interface PrevisionViewProps {
  /** Activas + cerradas (2020 en adelante) */
  historico: Convocatoria[];
  /** null = cargando; false = el backend no responde */
  disponible: boolean | null;
  onSeleccionar: (c: Convocatoria) => void;
}

const MES_MS = 30.4375 * 86_400_000;
const FILAS_INICIALES = 12;

/** Nombre corto de un programa: el tema, sin años ni paréntesis, y el órgano como apoyo. */
function etiqueta(p: Programa) {
  const tema = p.nombre.replace(/\([^)]*\)/g, '').replace(/\b(19|20)\d{2}(\s*[-/]\s*\d{2,4})?\b/g, '').replace(/\s+/g, ' ').trim();
  return { tema: tema.length > 70 ? `${tema.slice(0, 68)}…` : tema, organo: p.organismo.split(' - ')[0] };
}

const tono = (f: number) => (f >= 70 ? 'bg-brand' : f >= 50 ? 'bg-brand/60' : 'bg-brand/25');

/** Mes de la rejilla (0 = este mes) en que se prevé la apertura. Los retrasados caen en la primera columna. */
const columnaDe = (p: Programa, hoy: Date) => Math.max(0, Math.floor((p.proxima.getTime() - hoy.getTime()) / MES_MS));

/**
 * Previsión de aperturas (programas que se repiten cada año). Es una estimación, no una convocatoria:
 * por eso solo se muestra cuándo es probable que salga y con qué fiabilidad, sin los datos económicos.
 */
export function PrevisionView({ historico, disponible, onSeleccionar }: PrevisionViewProps) {
  const [verPocoFiables, setVerPocoFiables] = useState(false);
  const [verTodos, setVerTodos] = useState(false);
  const [programa, setPrograma] = useState<Programa | null>(null);
  const hoy = useMemo(() => new Date(), []);

  const programas = useMemo(() => (historico.length ? detectarProgramas(historico, hoy) : []), [historico, hoy]);
  const enCurso = programas.filter((p) => p.abierta);
  // Dentro de los próximos 12 meses, los más fiables primero
  const previstos = useMemo(
    () =>
      programas
        .filter((p) => !p.abierta && columnaDe(p, hoy) < 12 && (verPocoFiables || p.fiabilidad >= 50))
        .sort((a, b) => b.fiabilidad - a.fiabilidad || a.proxima.getTime() - b.proxima.getTime()),
    [programas, hoy, verPocoFiables]
  );
  const ocultosPocoFiables = programas.filter((p) => !p.abierta && columnaDe(p, hoy) < 12 && p.fiabilidad < 50).length;
  const meses = Array.from({ length: 12 }, (_, i) => new Date(hoy.getFullYear(), hoy.getMonth() + i, 1));
  const porMes = meses.map((_, i) => previstos.filter((p) => columnaDe(p, hoy) === i));
  const maxMes = Math.max(1, ...porMes.map((l) => l.length));
  const visibles = verTodos ? previstos : previstos.slice(0, FILAS_INICIALES);
  const proximos3 = previstos.filter((p) => columnaDe(p, hoy) < 3).length;

  if (disponible === null) return <p className="py-16 text-center text-sm text-zinc-400">Cargando el histórico…</p>;
  if (!disponible || historico.length === 0) {
    return (
      <div className="border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500">
        <History className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
        La previsión se calcula con el histórico del backend, que ahora mismo no está disponible.
      </div>
    );
  }
  if (programas.length === 0) {
    return <p className="border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500">Aún no hay programas con ediciones en al menos dos años distintos.</p>;
  }

  return (
    <div className="space-y-8">
      {/* Cifras clave */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-zinc-200 border border-zinc-200">
        {[
          { n: programas.length, t: 'Programas que se repiten', s: 'detectados en el histórico' },
          { n: proximos3, t: 'Próximos 3 meses', s: 'con apertura probable' },
          { n: previstos.filter((p) => p.fiabilidad >= 70).length, t: 'Muy fiables', s: 'se repiten cada año en el mismo mes' },
          { n: enCurso.length, t: 'Ya abiertos', s: 'edición de este año en curso' },
        ].map((k) => (
          <div key={k.t} className="bg-white p-4">
            <span className="font-serif text-3xl font-bold text-zinc-900">{k.n}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">{k.t}</span>
            <span className="block text-xs text-zinc-500">{k.s}</span>
          </div>
        ))}
      </div>

      {/* Cuándo llega la carga */}
      <section>
        <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Aperturas probables por mes</h3>
        <div className="flex items-end gap-2 border border-zinc-200 bg-white px-4 pt-4 pb-2">
          {meses.map((m, i) => {
            const l = porMes[i];
            const alta = l.filter((p) => p.fiabilidad >= 70).length;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1 text-xs text-zinc-500" title={`${l.length} programas previstos en ${nombreMes(m.getMonth() + 1)}`}>
                <span className="font-semibold text-zinc-700 h-4">{l.length || ''}</span>
                <span className="w-full h-24 flex flex-col justify-end">
                  <span className="w-full bg-brand/30" style={{ height: `${((l.length - alta) / maxMes) * 100}%` }} />
                  <span className="w-full bg-brand" style={{ height: `${(alta / maxMes) * 100}%` }} />
                </span>
                <span className={`capitalize ${i === 0 ? 'font-bold text-zinc-900' : ''}`}>{nombreMes(m.getMonth() + 1).slice(0, 3)}</span>
              </div>
            );
          })}
        </div>
        <p className="mt-2 flex items-center gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-2"><span className="h-3 w-3 bg-brand" /> muy fiable</span>
          <span className="flex items-center gap-2"><span className="h-3 w-3 bg-brand/30" /> fiable o menos</span>
        </p>
      </section>

      {/* Programas ordenados por fiabilidad */}
      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Los más probables · calendario de los próximos 12 meses</h3>
          {ocultosPocoFiables > 0 && (
            <button onClick={() => setVerPocoFiables((v) => !v)} className="text-xs font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-900 underline">
              {verPocoFiables ? 'Ocultar poco fiables' : `Mostrar ${ocultosPocoFiables} poco fiables`}
            </button>
          )}
        </div>
        <div className="border border-zinc-200 bg-white overflow-x-auto">
          <div className="min-w-[860px]">
            <div className="grid grid-cols-[minmax(260px,1fr)_repeat(12,44px)_90px] items-center border-b border-zinc-200 bg-zinc-50 text-[11px] uppercase text-zinc-500">
              <span className="p-2 pl-4">Programa</span>
              {meses.map((m, i) => (
                <span key={i} className={`text-center ${i === 0 ? 'font-bold text-zinc-900' : ''}`}>{nombreMes(m.getMonth() + 1).slice(0, 3)}</span>
              ))}
              <span className="text-right pr-4">Fiabilidad</span>
            </div>
            {visibles.map((p) => {
              const col = columnaDe(p, hoy);
              const e = etiqueta(p);
              return (
                <button
                  key={p.clave}
                  onClick={() => setPrograma(p)}
                  className="w-full grid grid-cols-[minmax(260px,1fr)_repeat(12,44px)_90px] items-center border-b border-zinc-100 text-left hover:bg-zinc-50"
                  title={`${p.nombre}\nSuele publicarse en ${nombreMes(p.mesApertura)} · ${p.anios.length} años con edición`}
                >
                  <span className="p-2 pl-4 min-w-0">
                    <span className="block text-sm font-semibold text-zinc-900 truncate">{e.tema}</span>
                    <span className="block text-[11px] text-zinc-500 truncate">{e.organo}</span>
                  </span>
                  {meses.map((_, i) => (
                    <span key={i} className="flex justify-center">
                      {i === col && (
                        <span className={`h-6 w-9 rounded-sm ${tono(p.fiabilidad)} ${p.retrasada ? 'ring-2 ring-amber-500 ring-offset-1' : ''}`} title={p.retrasada ? 'Debería haber salido ya' : undefined} />
                      )}
                    </span>
                  ))}
                  <span className="pr-4 flex items-center justify-end gap-2">
                    <span className="h-1.5 w-10 bg-zinc-100"><span className={`block h-full ${tono(p.fiabilidad)}`} style={{ width: `${p.fiabilidad}%` }} /></span>
                    <span className="w-8 text-right text-xs font-bold text-zinc-700">{p.fiabilidad}%</span>
                  </span>
                </button>
              );
            })}
            {previstos.length === 0 && <p className="p-8 text-center text-sm text-zinc-400">Ningún programa tiene apertura probable en los próximos 12 meses con este nivel de fiabilidad.</p>}
          </div>
        </div>
        {previstos.length > FILAS_INICIALES && (
          <button onClick={() => setVerTodos((v) => !v)} className="mt-3 rounded-full border border-zinc-300 px-6 py-2.5 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
            {verTodos ? 'Ver menos' : `Ver los ${previstos.length - FILAS_INICIALES} restantes`}
          </button>
        )}
        <p className="mt-3 text-xs text-zinc-400 leading-relaxed">
          Estimación a partir de las ediciones anteriores: la fiabilidad sube cuando un programa sale varios años y siempre en el mismo mes. Un recuadro con borde ámbar indica que ya debería haber salido y no consta. Pulsa una fila para ver su ficha.
        </p>
      </section>

      <ProgramaDrawer
        programa={programa}
        onClose={() => setPrograma(null)}
        onVerEdicion={(c) => {
          setPrograma(null);
          onSeleccionar(c);
        }}
      />
    </div>
  );
}
