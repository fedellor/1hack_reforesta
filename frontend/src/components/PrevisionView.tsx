'use client';

import React, { useMemo, useState } from 'react';
import { History } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { ETIQUETA_TRAMO, esAccionable, ORDEN_TRAMO, Programa, Tramo, detectarProgramas, evaluarPrevision, mesEnArco, nombreMes } from '@/lib/recurrencia';
import { ProgramaDrawer } from '@/components/ProgramaDrawer';
import { formatoEuros } from '@/lib/territorio';
import { temaDePrograma } from '@/lib/texto';

interface PrevisionViewProps {
  /** Activas + cerradas (2020 en adelante) */
  historico: Convocatoria[];
  /** null = cargando; false = el backend no responde */
  disponible: boolean | null;
  onSeleccionar: (c: Convocatoria) => void;
}

const MES_MS = 30.4375 * 86_400_000;
const MUESTRA_MINIMA = 10;

/** Nombre corto de un programa: el tema, sin años ni paréntesis, y el órgano como apoyo. */
function etiqueta(p: Programa) {
  const tema = temaDePrograma(p.nombre);
  return { tema: tema.length > 80 ? `${tema.slice(0, 78)}…` : tema, organo: (() => { const o = p.organismo.split(' - ').slice(0, 2).join(' · '); return o.length > 64 ? `${o.slice(0, 62)}…` : o; })() };
}

const CHIP: Record<Tramo, string> = { alta: 'bg-brand text-white', media: 'bg-emerald-100 text-emerald-900', baja: 'bg-zinc-100 text-zinc-600' };
const pct = (a: number, b: number) => (b ? `${Math.round((100 * a) / b)}%` : '–');

/** Mes de la rejilla (0 = este mes) en que se prevé el inicio de la ventana. Si hoy ya estamos dentro, cae en la primera columna. */
const columnaInicio = (p: Programa, hoy: Date) => Math.max(0, Math.floor((p.proxima.getTime() - hoy.getTime()) / MES_MS));

/**
 * Previsión de aperturas (programas que se repiten cada año). Es una estimación, no una convocatoria:
 * se muestra cuándo es probable que salga y con qué probabilidad, sin los datos económicos, y se mide su acierto con el histórico.
 */
export function PrevisionView({ historico, disponible, onSeleccionar }: PrevisionViewProps) {
  const [verMasOrganismos, setVerMasOrganismos] = useState(false);
  const [programa, setPrograma] = useState<Programa | null>(null);
  const hoy = useMemo(() => new Date(), []);
  const siguiente = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 1); // por defecto, el mes que viene
  const [anio, setAnio] = useState(siguiente.getFullYear());
  const [mes, setMes] = useState(siguiente.getMonth()); // 0-11

  const programas = useMemo(() => (historico.length ? detectarProgramas(historico, hoy) : []), [historico, hoy]);
  const evaluacion = useMemo(() => (historico.length ? evaluarPrevision(historico, hoy) : null), [historico, hoy]);
  // Solo programas en los que alguna edición fue apta para Reforesta: no sirve prever lo que no se podría pedir
  const candidatos = programas.filter((p) => !p.abierta && columnaInicio(p, hoy) < 12 && esAccionable(p));
  const previstos = useMemo(
    () =>
      candidatos
        .filter((p) => p.tramo !== 'baja')
        .sort((a, b) => ORDEN_TRAMO[a.tramo] - ORDEN_TRAMO[b.tramo] || b.anios.length - a.anios.length || a.proxima.getTime() - b.proxima.getTime()),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [programas, hoy]
  );
  const meses = Array.from({ length: 12 }, (_, i) => new Date(hoy.getFullYear(), hoy.getMonth() + i, 1));
  // Un programa «pesa» en cada mes cubierto por su ventana prevista
  const cubre = (p: Programa, m: Date) => mesEnArco(m.getMonth() + 1, p.mesDesde, p.mesHasta, 0);
  const porMes = meses.map((m) => previstos.filter((p) => cubre(p, m)));
  const maxMes = Math.max(1, ...porMes.map((l) => l.length));
  // Lo que suele salir en el mes elegido, agrupado por organismo
  const mesSel = new Date(anio, mes, 1);
  const mover = (delta: number) => {
    const d = new Date(anio, mes + delta, 1);
    setAnio(d.getFullYear());
    setMes(d.getMonth());
    setVerMasOrganismos(false);
  };
  const campo = 'appearance-none text-center px-5 py-2 border border-zinc-200 bg-white text-sm font-semibold capitalize text-zinc-800 focus:outline-hidden focus:border-zinc-500 rounded-full';
  const delMes = previstos.filter((p) => cubre(p, mesSel));
  const grupos = useMemo(() => {
    const g = new Map<string, Programa[]>();
    delMes.forEach((p) => g.set(etiqueta(p).organo, [...(g.get(etiqueta(p).organo) ?? []), p]));
    return [...g.entries()].sort(
      (a, b) => Math.min(...a[1].map((p) => ORDEN_TRAMO[p.tramo])) - Math.min(...b[1].map((p) => ORDEN_TRAMO[p.tramo])) || b[1].length - a[1].length
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previstos, anio, mes]);
  const altos = delMes.filter((p) => p.tramo === 'alta').length;
  const importeTop = Math.max(0, ...delMes.map((p) => p.cuantiaMedia));
  const GRUPOS_VISIBLES = 6;

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

      {/* Resumen del mes: qué suele salir, quién y en qué consiste */}
      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Qué suele salir según el histórico</h3>
          <div className="flex items-center gap-2">
            <button onClick={() => mover(-1)} aria-label="Mes anterior" className="h-9 w-9 rounded-full border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50">‹</button>
            <select value={mes} onChange={(e) => { setMes(Number(e.target.value)); setVerMasOrganismos(false); }} className={campo} aria-label="Mes">
              {Array.from({ length: 12 }, (_, m) => <option key={m} value={m}>{nombreMes(m + 1)}</option>)}
            </select>
            <select value={anio} onChange={(e) => { setAnio(Number(e.target.value)); setVerMasOrganismos(false); }} className={campo} aria-label="Año">
              {[hoy.getFullYear(), hoy.getFullYear() + 1, hoy.getFullYear() + 2].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <button onClick={() => mover(1)} aria-label="Mes siguiente" className="h-9 w-9 rounded-full border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50">›</button>
            {!(anio === siguiente.getFullYear() && mes === siguiente.getMonth()) && (
              <button onClick={() => { setAnio(siguiente.getFullYear()); setMes(siguiente.getMonth()); setVerMasOrganismos(false); }} className="ml-1 text-xs font-semibold uppercase tracking-wide text-zinc-600 underline hover:text-zinc-900">Mes que viene</button>
            )}
          </div>
        </div>

        {delMes.length === 0 ? (
          <p className="border border-dashed border-zinc-300 p-6 text-center text-sm text-zinc-500">
            El histórico no apunta a ningún programa con ventana en {nombreMes(mesSel.getMonth() + 1)}.
          </p>
        ) : (
          <>
            <p className="mb-4 text-sm text-zinc-700 leading-relaxed">
              En <strong className="capitalize text-zinc-900">{nombreMes(mesSel.getMonth() + 1)}</strong> suelen abrir{' '}
              <strong className="text-zinc-900">{delMes.length} {delMes.length === 1 ? 'programa' : 'programas'}</strong> de{' '}
              <strong className="text-zinc-900">{grupos.length} {grupos.length === 1 ? 'organismo' : 'organismos'}</strong>
              {altos > 0 ? <>, {altos} con probabilidad alta</> : null}
              {importeTop > 0 ? <>. Las ayudas más grandes rondan los <strong className="text-zinc-900">{formatoEuros(importeTop)}</strong> por proyecto</> : null}.
              {' '}Aún no están confirmadas: las que ya tienen fecha están en Plan de ataque.
            </p>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {(verMasOrganismos ? grupos : grupos.slice(0, GRUPOS_VISIBLES)).map(([organo, lista]) => (
                <div key={organo} className="border border-zinc-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-bold text-zinc-900 leading-snug">{organo}</span>
                    <span className="shrink-0 text-xs text-zinc-400">{lista.length}</span>
                  </div>
                  <ul className="mt-2 space-y-2">
                    {lista.slice(0, 3).map((p) => (
                      <li key={p.clave}>
                        <button onClick={() => setPrograma(p)} className="w-full text-left group">
                          <span className="flex items-start gap-2">
                            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${p.tramo === 'alta' ? 'bg-brand' : 'bg-brand/40'}`} title={`Probabilidad ${ETIQUETA_TRAMO[p.tramo].toLowerCase()}`} />
                            <span className="min-w-0">
                              <span className="block text-xs text-zinc-800 leading-snug line-clamp-2 group-hover:underline">{etiqueta(p).tema}</span>
                              {(p.cuantiaMedia > 0 || p.ventanaDias) && (
                                <span className="block text-[11px] text-zinc-500">
                                  {p.cuantiaMedia > 0 && <>≈ {formatoEuros(p.cuantiaMedia)}</>}
                                  {p.cuantiaMedia > 0 && p.ventanaDias ? ' · ' : ''}
                                  {p.ventanaDias ? <>plazo ≈ {p.ventanaDias} d</> : null}
                                </span>
                              )}
                            </span>
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                  {lista.length > 3 && <p className="mt-2 text-[11px] text-zinc-400">+{lista.length - 3} más de este organismo</p>}
                </div>
              ))}
            </div>
            {grupos.length > GRUPOS_VISIBLES && (
              <button onClick={() => setVerMasOrganismos((v) => !v)} className="mt-3 text-xs font-semibold uppercase tracking-wide text-zinc-500 underline hover:text-zinc-900">
                {verMasOrganismos ? 'Ver menos organismos' : `Ver ${grupos.length - GRUPOS_VISIBLES} organismos más`}
              </button>
            )}
            <p className="mt-3 flex items-center gap-4 text-xs text-zinc-400">
              <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-brand" /> probabilidad alta</span>
              <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-brand/40" /> media</span>
              <span>Pulsa un programa para ver cuándo salió cada año.</span>
            </p>
          </>
        )}
      </section>

      {/* Cómo de fiable es: se mide con el propio histórico */}
      <section className="border border-zinc-200 bg-zinc-50 p-5">
        <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">¿Cuánto acierta esta previsión?</h3>
        {evaluacion && evaluacion.total.n >= MUESTRA_MINIMA ? (
          <>
            <p className="mt-2 text-sm text-zinc-700 leading-relaxed">
              Probada con el propio histórico ({evaluacion.anios[0]}–{evaluacion.anios[evaluacion.anios.length - 1]}): cada año se hizo la previsión con lo que se sabía a 1 de enero y se comparó con lo que salió.
            </p>
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-px bg-zinc-200 border border-zinc-200">
              {(['alta', 'media'] as const).map((t) => {
                const a = evaluacion.porTramo[t];
                return (
                  <div key={t} className="bg-white p-3">
                    <span className={`inline-block rounded-full px-3 py-0.5 text-[11px] font-bold uppercase ${CHIP[t]}`}>{ETIQUETA_TRAMO[t]}</span>
                    <span className="block mt-1 font-serif text-2xl font-bold text-zinc-900">{pct(a.enAnio, a.n)}</span>
                    <span className="block text-xs text-zinc-500">
                      salieron ese año ({a.enAnio} de {a.n}){a.enAnio >= 10 ? <> · {pct(a.mesEnVentana, a.enAnio)} de ellas, dentro de la ventana prevista</> : null}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-xs text-zinc-500 leading-relaxed">
              No es una promesa: es la proporción que se cumplió en el pasado con lo que el radar tiene capturado. Se recalcula sola al cargar más datos. Las de probabilidad baja no se muestran porque casi nunca se cumplen.
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
