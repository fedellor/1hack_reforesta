'use client';

import React, { useMemo, useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros, formatoImporte } from '@/lib/territorio';
import { aperturaISO, diasHastaApertura, esProxima, plazoSinFijar } from '@/lib/plazo';
import { esCitaLiteral, limpiarJustificacion } from '@/lib/texto';

interface PlanViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

/** Días de preparación estimados de una solicitud (supuesto de trabajo, editable). */
const PREPARACION_DIAS = 14;
const RANGOS = [30, 60, 90, 180, 365] as const;
const FILAS_INICIALES = 12;

const colorBarra = (dias: number) => (dias < 7 ? 'bg-rose-500' : dias < 20 ? 'bg-amber-500' : 'bg-brand');
const fechaCorta = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
const ETIQUETA_ESTADO: Record<string, string> = { en_preparacion: 'En preparación', presentada: 'Presentada' };

function motivoDe(c: Convocatoria): { texto: string; cita: boolean } {
  if (!c.elegible) return { texto: `Excluida: ${c.dealbreakers[0] ?? c.motivoElegibilidad}`, cita: false };
  const literal = c.citasBasesJustificacion.find(esCitaLiteral);
  if (literal) return { texto: literal, cita: true };
  return { texto: c.citasBasesJustificacion[0] ? limpiarJustificacion(c.citasBasesJustificacion[0]) : '', cita: false };
}

/** Columna izquierda de cada fila: lo necesario para decidir sin abrir la ficha. */
function Descripcion({ c, aviso }: { c: Convocatoria; aviso?: React.ReactNode }) {
  const motivo = motivoDe(c);
  const estadoEquipo = ETIQUETA_ESTADO[c.estadoInterno];
  return (
    <div className="p-3 pr-5 min-w-0">
      <span className="block text-[11px] text-zinc-500 truncate">
        {c.organismo}{c.organismo.includes(c.ambitoTerritorial) ? '' : ` · ${c.ambitoTerritorial}`}
      </span>
      <span className="text-sm font-semibold text-zinc-900 leading-snug line-clamp-2 group-hover:text-emerald-800">{c.titulo}</span>
      <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-zinc-600">
        <strong className="text-zinc-900">{formatoImporte(c.cuantiaMaximaProyecto)}</strong>
        <span>· {c.porcentajeCofinanciacion === 0 ? '100% financiado' : `aportas ${c.porcentajeCofinanciacion}%`}</span>
        <span>· encaje <strong className="text-zinc-900">{c.matchingGlobal}%</strong></span>
        {!c.elegible && <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">Excluida</span>}
        {estadoEquipo && <span className="rounded-full bg-zinc-900 px-2 py-0.5 text-[10px] font-bold uppercase text-white">{estadoEquipo}</span>}
        {aviso}
      </span>
      {motivo.texto && (
        <span className={`mt-1 text-xs line-clamp-1 border-l-2 pl-2 ${c.elegible ? `border-brand text-zinc-500 ${motivo.cita ? 'italic' : ''}` : 'border-rose-400 text-rose-700'}`}>
          {motivo.cita ? `“${motivo.texto}”` : motivo.texto}
        </span>
      )}
    </div>
  );
}

/**
 * Plan de ataque: una sola vista con lo que se puede pedir ya (abiertas) y lo que está confirmado pero aún no abre.
 * Ambos bloques comparten eje de tiempo; un único selector de horizonte sustituye a la lista y al calendario.
 */
export function PlanView({ convocatorias, onSeleccionar }: PlanViewProps) {
  const [rango, setRango] = useState<(typeof RANGOS)[number]>(60);
  const [verTodas, setVerTodas] = useState(false);
  const hoy = useMemo(() => new Date(), []);

  const abiertas = useMemo(
    () => convocatorias.filter((c) => !esProxima(c) && !plazoSinFijar(c) && c.diasRestantes >= 0 && c.diasRestantes <= rango).sort((a, b) => a.diasRestantes - b.diasRestantes),
    [convocatorias, rango]
  );
  const proximas = useMemo(
    () => convocatorias.filter((c) => esProxima(c) && diasHastaApertura(c) <= rango).sort((a, b) => diasHastaApertura(a) - diasHastaApertura(b)),
    [convocatorias, rango]
  );
  const sinPlazo = useMemo(() => convocatorias.filter((c) => !esProxima(c) && plazoSinFijar(c)).sort((a, b) => b.matchingGlobal - a.matchingGlobal), [convocatorias]);
  const visibles = verTodas ? abiertas : abiertas.slice(0, FILAS_INICIALES);

  // Eje: semanas hasta 90 días, meses a partir de ahí
  const paso = rango <= 90 ? 7 : 30;
  const columnas = Math.ceil(rango / paso);
  const porColumna = Array.from({ length: columnas }, (_, i) => abiertas.filter((c) => Math.floor(c.diasRestantes / paso) === i));
  const maxColumna = Math.max(1, ...porColumna.map((l) => l.length));
  const cargaMax = porColumna.reduce((mejor, l, i) => (l.length > porColumna[mejor].length ? i : mejor), 0);
  const empezarYa = abiertas.filter((c) => c.diasRestantes <= PREPARACION_DIAS).length;
  const en7 = abiertas.filter((c) => c.diasRestantes <= 7).length;
  const visiblesEnHorizonte = [...abiertas, ...proximas, ...sinPlazo];
  const dinero = visiblesEnHorizonte.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const fueraDeHorizonte = convocatorias.filter(
    (c) =>
      (!esProxima(c) && !plazoSinFijar(c) && c.diasRestantes > rango) ||
      (esProxima(c) && diasHastaApertura(c) > rango)
  );

  const fechaColumna = (i: number) => {
    const d = new Date(hoy);
    d.setDate(d.getDate() + i * paso);
    return d.toLocaleDateString('es-ES', paso === 7 ? { day: 'numeric', month: 'short' } : { month: 'short', year: '2-digit' });
  };
  const pct = (dias: number) => `${Math.max(0, Math.min(100, (dias / rango) * 100))}%`;
  const rejilla = (
    <div className="absolute inset-0 grid pointer-events-none" style={{ gridTemplateColumns: `repeat(${columnas}, 1fr)` }}>
      {porColumna.map((_, i) => <div key={i} className="border-l border-zinc-100" />)}
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-wrap gap-x-8 gap-y-2">
          <div>
            <span className="font-serif text-3xl font-bold text-rose-600">{empezarYa}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">Hay que empezar ya</span>
            <span className="block text-xs text-zinc-500">cierran en {PREPARACION_DIAS} días o menos</span>
          </div>
          <div>
            <span className="font-serif text-3xl font-bold text-zinc-900">{en7}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">Cierran esta semana</span>
            <span className="block text-xs text-zinc-500">en los próximos 7 días</span>
          </div>
          <div>
            <span className="font-serif text-3xl font-bold text-zinc-900">{proximas.length}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">Por abrir</span>
            <span className="block text-xs text-zinc-500">confirmadas, abren en {rango} días</span>
          </div>
          <div>
            <span className="font-serif text-3xl font-bold text-zinc-900">{formatoEuros(dinero)}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">En juego</span>
            <span className="block text-xs text-zinc-500">
              {abiertas.length} abiertas · {proximas.length} por abrir
              {sinPlazo.length > 0 ? ` · ${sinPlazo.length} sin plazo` : ''}
              {fueraDeHorizonte.length > 0
                ? ` (+${fueraDeHorizonte.length} fuera de ${rango === 365 ? '1 año' : `${rango} d`})`
                : ''}
            </span>
          </div>
        </div>
        <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1">
          {RANGOS.map((r) => (
            <button key={r} onClick={() => setRango(r)} className={`px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-wide transition-colors ${rango === r ? 'bg-[#333] text-white' : 'text-zinc-600 hover:text-zinc-900'}`}>
              {r === 365 ? '1 año' : `${r} días`}
            </button>
          ))}
        </div>
      </div>

      <div className="border border-zinc-200 bg-white overflow-x-auto">
        <div className="min-w-[940px]">
          {/* Abiertas */}
          <div className="grid grid-cols-[400px_1fr] border-b border-zinc-200 bg-zinc-50">
            <div className="p-3 self-end">
              <span className="block text-xs font-bold uppercase tracking-[0.15em] text-brand">Abiertas · se pueden solicitar ya</span>
              <span className="block text-[11px] text-zinc-500">Cierres por {paso === 7 ? 'semana' : 'mes'} · el mayor pico: {fechaColumna(cargaMax)}</span>
            </div>
            <div className="relative h-20">
              <div className="absolute inset-0 grid" style={{ gridTemplateColumns: `repeat(${columnas}, 1fr)` }}>
                {porColumna.map((l, i) => (
                  <div key={i} className="relative border-l border-zinc-200 flex flex-col justify-end items-center pb-6 px-0.5">
                    {l.length > 0 && (
                      <>
                        <span className="text-xs font-bold text-zinc-700">{l.length}</span>
                        <span className={`w-full max-w-[28px] ${i === cargaMax ? 'bg-zinc-900' : 'bg-zinc-300'}`} style={{ height: `${(l.length / maxColumna) * 32}px` }} />
                      </>
                    )}
                    {(columnas <= 13 || i % 2 === 0) && <span className="absolute bottom-1 left-1 text-[10px] text-zinc-500">{fechaColumna(i)}</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {visibles.map((c) => {
            const inicioPrep = Math.max(0, c.diasRestantes - PREPARACION_DIAS);
            const urgente = c.diasRestantes <= PREPARACION_DIAS && c.elegible;
            return (
              <button key={c.id} onClick={() => onSeleccionar(c)} className={`w-full grid grid-cols-[400px_1fr] border-b border-zinc-100 text-left hover:bg-zinc-50 group ${!c.elegible ? 'bg-zinc-50' : ''}`}>
                <Descripcion c={c} aviso={urgente ? <span className="font-bold text-rose-600">EMPEZAR YA</span> : undefined} />
                <div className="relative">
                  {rejilla}
                  {inicioPrep > 0 && <span className="absolute top-1/2 -translate-y-1/2 h-2 bg-emerald-100" style={{ left: 0, width: pct(inicioPrep) }} />}
                  <span className={`absolute top-1/2 -translate-y-1/2 h-4 ${colorBarra(c.diasRestantes)}`} style={{ left: pct(inicioPrep), width: `calc(${pct(c.diasRestantes)} - ${pct(inicioPrep)})`, minWidth: 6 }} />
                  <span className="absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 -translate-x-1/2 rotate-45 bg-zinc-900" style={{ left: pct(c.diasRestantes) }} />
                  <span
                    className="absolute top-1/2 -translate-y-1/2 text-xs font-semibold text-zinc-700 whitespace-nowrap"
                    style={c.diasRestantes / rango > 0.8 ? { right: `calc(${100 - Math.min(100, (c.diasRestantes / rango) * 100)}% + 14px)` } : { left: `calc(${pct(c.diasRestantes)} + 14px)` }}
                  >
                    cierra {fechaCorta(c.fechaCierre)} · {c.diasRestantes} d
                  </span>
                </div>
              </button>
            );
          })}
          {abiertas.length === 0 && <p className="p-6 text-center text-sm text-zinc-400">No hay cierres en {rango === 365 ? '1 año' : `${rango} días`} con los filtros actuales. Prueba con un horizonte mayor.</p>}

          {/* Confirmadas pero aún sin abrir */}
          <div className="grid grid-cols-[400px_1fr] border-y border-zinc-200 bg-zinc-50">
            <div className="p-3">
              <span className="block text-xs font-bold uppercase tracking-[0.15em] text-sky-700">Por abrir · confirmadas</span>
              <span className="block text-[11px] text-zinc-500">Bases publicadas; el plazo de solicitud aún no ha empezado</span>
            </div>
            <div className="relative h-12">
              <div className="absolute inset-0 grid" style={{ gridTemplateColumns: `repeat(${columnas}, 1fr)` }}>
                {porColumna.map((_, i) => (
                  <div key={i} className="relative border-l border-zinc-200">
                    {(columnas <= 13 || i % 2 === 0) && <span className="absolute bottom-1 left-1 text-[10px] text-zinc-500">{fechaColumna(i)}</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {proximas.map((c) => {
            const abre = diasHastaApertura(c);
            const ini = aperturaISO(c);
            return (
              <button key={c.id} onClick={() => onSeleccionar(c)} className="w-full grid grid-cols-[400px_1fr] border-b border-zinc-100 text-left hover:bg-zinc-50 group">
                <Descripcion c={c} aviso={<span className="font-semibold text-sky-700">abre en {abre} d</span>} />
                <div className="relative">
                  {rejilla}
                  {/* Aún cerrada */}
                  <span className="absolute top-1/2 -translate-y-1/2 h-0 border-t-2 border-dashed border-zinc-300" style={{ left: 0, width: pct(abre) }} />
                  {/* Ventana de solicitud */}
                  <span className="absolute top-1/2 -translate-y-1/2 h-4 border-2 border-sky-500 bg-sky-100" style={{ left: pct(abre), width: `calc(${pct(Math.min(rango, c.diasRestantes))} - ${pct(abre)})`, minWidth: 6 }} />
                  {c.diasRestantes <= rango && <span className="absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 -translate-x-1/2 rotate-45 bg-zinc-900" style={{ left: pct(c.diasRestantes) }} />}
                  <span
                    className="absolute top-1/2 -translate-y-1/2 text-xs font-semibold text-zinc-700 whitespace-nowrap"
                    style={Math.min(rango, c.diasRestantes) / rango > 0.7 ? { right: `calc(${100 - Math.min(100, (abre / rango) * 100)}% + 8px)` } : { left: `calc(${pct(Math.min(rango, c.diasRestantes))} + 14px)` }}
                  >
                    {ini ? `abre ${fechaCorta(ini)}` : 'por abrir'} · cierra {fechaCorta(c.fechaCierre)}
                  </span>
                </div>
              </button>
            );
          })}
          {proximas.length === 0 && <p className="p-6 text-center text-sm text-zinc-400">Ninguna convocatoria confirmada abre en {rango === 365 ? '1 año' : `${rango} días`}.</p>}
        </div>
      </div>

      {abiertas.length > FILAS_INICIALES && (
        <button onClick={() => setVerTodas((v) => !v)} className="rounded-full border border-zinc-300 px-6 py-3 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
          {verTodas ? 'Ver menos' : `Ver las ${abiertas.length - FILAS_INICIALES} abiertas restantes`}
        </button>
      )}

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-zinc-500">
        <span className="flex items-center gap-2"><span className="h-2 w-6 bg-emerald-100" /> margen para decidir</span>
        <span className="flex items-center gap-2"><span className="h-4 w-6 bg-brand" /> preparación estimada ({PREPARACION_DIAS} d) · rojo si quedan menos de 7 d, ámbar menos de 20 d</span>
        <span className="flex items-center gap-2"><span className="h-4 w-6 border-2 border-sky-500 bg-sky-100" /> ventana de solicitud de una convocatoria por abrir</span>
        <span className="flex items-center gap-2"><span className="h-3 w-3 rotate-45 bg-zinc-900" /> cierre</span>
      </div>

      {sinPlazo.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Abiertas sin plazo fijado ({sinPlazo.length})</h3>
          <ul className="divide-y divide-zinc-200 border border-zinc-200 bg-white">
            {sinPlazo.map((c) => (
              <li key={c.id}>
                <button onClick={() => onSeleccionar(c)} className="w-full text-left flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-50">
                  <span className="min-w-0">
                    <span className="block text-xs text-zinc-500 truncate">{c.organismo}</span>
                    <span className="text-sm font-semibold text-zinc-900 line-clamp-1">{c.titulo}</span>
                  </span>
                  <span className="shrink-0 text-right text-xs text-zinc-600">
                    <strong className="block text-sm text-zinc-900">{formatoImporte(c.cuantiaMaximaProyecto)}</strong>
                    encaje {c.matchingGlobal}%
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
