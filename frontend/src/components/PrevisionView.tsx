'use client';

import React, { useMemo, useState } from 'react';
import { History } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { ETIQUETA_TRAMO, ORDEN_TRAMO, Programa, Tramo, detectarProgramas, evaluarPrevision, mesEnArco, nombreMes, textoVentana } from '@/lib/recurrencia';
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
const MUESTRA_MINIMA = 10;

/** Nombre corto de un programa: el tema, sin años ni paréntesis, y el órgano como apoyo. */
function etiqueta(p: Programa) {
  const tema = p.nombre.replace(/\([^)]*\)/g, '').replace(/\b(19|20)\d{2}(\s*[-/]\s*\d{2,4})?\b/g, '').replace(/\s+/g, ' ').trim();
  return { tema: tema.length > 70 ? `${tema.slice(0, 68)}…` : tema, organo: p.organismo.split(' - ')[0] };
}

const TONO: Record<Tramo, string> = { alta: 'bg-brand', media: 'bg-brand/55', baja: 'bg-brand/20' };
const CHIP: Record<Tramo, string> = { alta: 'bg-brand text-white', media: 'bg-emerald-100 text-emerald-900', baja: 'bg-zinc-100 text-zinc-600' };
const pct = (a: number, b: number) => (b ? `${Math.round((100 * a) / b)}%` : '–');

/** Mes de la rejilla (0 = este mes) en que se prevé el inicio de la ventana. Si hoy ya estamos dentro, cae en la primera columna. */
const columnaInicio = (p: Programa, hoy: Date) => Math.max(0, Math.floor((p.proxima.getTime() - hoy.getTime()) / MES_MS));

/**
 * Previsión de aperturas (programas que se repiten cada año). Es una estimación, no una convocatoria:
 * se muestra cuándo es probable que salga y con qué probabilidad, sin los datos económicos, y se mide su acierto con el histórico.
 */
export function PrevisionView({ historico, disponible, onSeleccionar }: PrevisionViewProps) {
  const [verPocoProbables, setVerPocoProbables] = useState(false);
  const [verTodos, setVerTodos] = useState(false);
  const [programa, setPrograma] = useState<Programa | null>(null);
  const hoy = useMemo(() => new Date(), []);

  const programas = useMemo(() => (historico.length ? detectarProgramas(historico, hoy) : []), [historico, hoy]);
  const evaluacion = useMemo(() => (historico.length ? evaluarPrevision(historico, hoy) : null), [historico, hoy]);
  const enCurso = programas.filter((p) => p.abierta);
  const candidatos = programas.filter((p) => !p.abierta && columnaInicio(p, hoy) < 12);
  const previstos = useMemo(
    () =>
      candidatos
        .filter((p) => verPocoProbables || p.tramo !== 'baja')
        .sort((a, b) => ORDEN_TRAMO[a.tramo] - ORDEN_TRAMO[b.tramo] || b.anios.length - a.anios.length || a.proxima.getTime() - b.proxima.getTime()),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [programas, hoy, verPocoProbables]
  );
  const ocultos = candidatos.filter((p) => p.tramo === 'baja').length;
  const meses = Array.from({ length: 12 }, (_, i) => new Date(hoy.getFullYear(), hoy.getMonth() + i, 1));
  // Un programa «pesa» en cada mes cubierto por su ventana prevista
  const cubre = (p: Programa, m: Date) => mesEnArco(m.getMonth() + 1, p.mesDesde, p.mesHasta, 0);
  const porMes = meses.map((m) => previstos.filter((p) => cubre(p, m)));
  const maxMes = Math.max(1, ...porMes.map((l) => l.length));
  const visibles = verTodos ? previstos : previstos.slice(0, FILAS_INICIALES);
  const probables = previstos.filter((p) => p.tramo === 'alta').length;
  const proximos3 = previstos.filter((p) => columnaInicio(p, hoy) < 3).length;

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
          { n: proximos3, t: 'Próximos 3 meses', s: 'con ventana de apertura prevista' },
          { n: probables, t: 'Muy probables', s: 'salieron el año pasado y llevan años repitiéndose' },
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
        <h3 className="mb-3 text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Programas con ventana de apertura prevista, por mes</h3>
        <div className="flex items-end gap-2 border border-zinc-200 bg-white px-4 pt-4 pb-2">
          {meses.map((m, i) => {
            const l = porMes[i];
            const alta = l.filter((p) => p.tramo === 'alta').length;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1 text-xs text-zinc-500" title={`${l.length} programas con ventana prevista en ${nombreMes(m.getMonth() + 1)}`}>
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
          <span className="flex items-center gap-2"><span className="h-3 w-3 bg-brand" /> probabilidad alta</span>
          <span className="flex items-center gap-2"><span className="h-3 w-3 bg-brand/30" /> media o baja</span>
        </p>
      </section>

      {/* Programas ordenados por probabilidad */}
      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Los más probables · ventanas de los próximos 12 meses</h3>
          {ocultos > 0 && (
            <button onClick={() => setVerPocoProbables((v) => !v)} className="text-xs font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-900 underline">
              {verPocoProbables ? 'Ocultar los poco probables' : `Mostrar ${ocultos} poco probables`}
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
              <span className="text-right pr-4">Probabilidad</span>
            </div>
            {visibles.map((p) => {
              const e = etiqueta(p);
              return (
                <button
                  key={p.clave}
                  onClick={() => setPrograma(p)}
                  className="w-full grid grid-cols-[minmax(260px,1fr)_repeat(12,44px)_90px] items-center border-b border-zinc-100 text-left hover:bg-zinc-50"
                  title={`${p.nombre}\nVentana habitual: ${textoVentana(p)} · ${p.anios.length} años con edición`}
                >
                  <span className="p-2 pl-4 min-w-0">
                    <span className="block text-sm font-semibold text-zinc-900 truncate">{e.tema}</span>
                    <span className="block text-[11px] text-zinc-500 truncate">{e.organo} · {textoVentana(p)}</span>
                  </span>
                  {meses.map((m, i) => (
                    <span key={i} className="flex justify-center">
                      {cubre(p, m) ? (
                        <span className={`h-6 w-full ${TONO[p.tramo]}`} />
                      ) : (
                        p.retrasada && i === 0 && <span className="h-3 w-3 rounded-full bg-amber-500" title="Su ventana de este año ya pasó y no consta la edición" />
                      )}
                    </span>
                  ))}
                  <span className="pr-4 flex justify-end">
                    <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide ${CHIP[p.tramo]}`}>{ETIQUETA_TRAMO[p.tramo]}</span>
                  </span>
                </button>
              );
            })}
            {previstos.length === 0 && <p className="p-8 text-center text-sm text-zinc-400">Ningún programa tiene ventana de apertura en los próximos 12 meses con este nivel de probabilidad.</p>}
          </div>
        </div>
        {previstos.length > FILAS_INICIALES && (
          <button onClick={() => setVerTodos((v) => !v)} className="mt-3 rounded-full border border-zinc-300 px-6 py-2.5 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
            {verTodos ? 'Ver menos' : `Ver los ${previstos.length - FILAS_INICIALES} restantes`}
          </button>
        )}
        <p className="mt-3 text-xs text-zinc-400 leading-relaxed">
          La banda marca los meses en que el programa ha salido en años anteriores. Un punto ámbar al inicio indica que la ventana de este año ya pasó y no consta la edición. Pulsa una fila para ver su ficha.
        </p>
      </section>

      {/* Cómo de fiable es: se mide con el propio histórico */}
      <section className="border border-zinc-200 bg-zinc-50 p-5">
        <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">¿Cuánto acierta esta previsión?</h3>
        {evaluacion && evaluacion.total.n >= MUESTRA_MINIMA ? (
          <>
            <p className="mt-2 text-sm text-zinc-700 leading-relaxed">
              Se ha probado con el propio histórico: para cada año ({evaluacion.anios[0]}–{evaluacion.anios[evaluacion.anios.length - 1]}) se hizo la previsión con lo que se sabía a 1 de enero y se comparó con lo que salió ({evaluacion.total.n} previsiones).
            </p>
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-px bg-zinc-200 border border-zinc-200">
              {(['alta', 'media', 'baja'] as const).map((t) => {
                const a = evaluacion.porTramo[t];
                return (
                  <div key={t} className="bg-white p-3">
                    <span className={`inline-block rounded-full px-3 py-0.5 text-[11px] font-bold uppercase ${CHIP[t]}`}>{ETIQUETA_TRAMO[t]}</span>
                    <span className="block mt-1 font-serif text-2xl font-bold text-zinc-900">{pct(a.enAnio, a.n)}</span>
                    <span className="block text-xs text-zinc-500">salieron ese año ({a.enAnio} de {a.n})</span>
                    {a.enAnio >= 5 && <span className="block text-xs text-zinc-500">y en la ventana prevista: {pct(a.mesEnVentana, a.enAnio)}</span>}
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-zinc-500 leading-relaxed">
              Lectura: «probabilidad alta» no significa seguro, sino la proporción que se cumplió en el pasado. El histórico solo contiene lo que el radar ha capturado; si faltan convocatorias, el acierto real es mayor. Esta medición se recalcula sola cuando se cargan más datos.
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-zinc-500">Todavía no hay histórico suficiente para medir el acierto (hacen falta al menos {MUESTRA_MINIMA} previsiones comprobables).</p>
        )}
      </section>

      <ProgramaDrawer
        programa={programa}
        evaluacion={evaluacion}
        onClose={() => setPrograma(null)}
        onVerEdicion={(c) => {
          setPrograma(null);
          onSeleccionar(c);
        }}
      />
    </div>
  );
}
