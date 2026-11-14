'use client';

import React, { useMemo, useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros, fondosDe, textoImporte } from '@/lib/territorio';
import { aperturaISO, esProxima, plazoSinFijar } from '@/lib/plazo';

interface PlanViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

/** Días de preparación estimados de una solicitud (supuesto de trabajo, editable). */
const PREPARACION_DIAS = 14;
const FILAS_INICIALES = 12;

const colorBarra = (dias: number) => (dias < 7 ? 'bg-rose-500' : dias < 20 ? 'bg-amber-500' : 'bg-brand');
const fechaCorta = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
const ETIQUETA_ESTADO: Record<string, string> = { en_preparacion: 'En preparación', presentada: 'Presentada' };

/** Columna izquierda de cada fila: lo justo para decidir sin abrir la ficha. */
function Descripcion({ c }: { c: Convocatoria }) {
  const estadoEquipo = ETIQUETA_ESTADO[c.estadoInterno];
  return (
    <div className="px-3 py-2.5 pr-5 min-w-0">
      <span className="block text-[11px] text-zinc-500 truncate">
        {c.organismo}{c.organismo.includes(c.ambitoTerritorial) ? '' : ` · ${c.ambitoTerritorial}`}
      </span>
      <span className="block text-sm font-semibold text-zinc-900 leading-snug line-clamp-2 group-hover:text-emerald-800">{c.titulo}</span>
      <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-zinc-600">
        <strong className="text-zinc-900">{textoImporte(c)}</strong>
        <span>· encaje <strong className="text-zinc-900">{c.matchingGlobal}%</strong></span>
        {!c.elegible && <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">Excluida</span>}
        {estadoEquipo && <span className="rounded-full bg-zinc-900 px-2 py-0.5 text-[10px] font-bold uppercase text-white">{estadoEquipo}</span>}
      </span>
    </div>
  );
}

/**
 * Plan de ataque: pensado para la urgencia. Se elige un mes y se ve qué cierra, día a día.
 * Las confirmadas que aún no han abierto aparecen en el mes en que abren, como aviso aparte de la tabla.
 */
export function PlanView({ convocatorias, onSeleccionar }: PlanViewProps) {
  const hoy = useMemo(() => {
    const d = new Date();
    d.setHours(12, 0, 0, 0);
    return d;
  }, []);
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [mes, setMes] = useState(hoy.getMonth()); // 0-11
  const [verTodas, setVerTodas] = useState(false);
  const [verSinPlazo, setVerSinPlazo] = useState(false);

  const esMesActual = anio === hoy.getFullYear() && mes === hoy.getMonth();
  const diasMes = new Date(anio, mes + 1, 0).getDate();
  const nombreMes = (m: number) => new Date(2000, m, 1).toLocaleDateString('es-ES', { month: 'long' });
  const enMes = (iso: string) => {
    const d = new Date(`${iso.slice(0, 10)}T12:00:00`);
    return d.getFullYear() === anio && d.getMonth() === mes;
  };
  const diaDe = (iso: string) => new Date(`${iso.slice(0, 10)}T12:00:00`).getDate();
  const mover = (delta: number) => {
    const d = new Date(anio, mes + delta, 1);
    setAnio(d.getFullYear());
    setMes(d.getMonth());
    setVerTodas(false);
  };

  const abiertas = useMemo(
    () =>
      convocatorias
        .filter((c) => !esProxima(c) && !plazoSinFijar(c) && c.diasRestantes >= 0 && enMes(c.fechaCierre))
        .sort((a, b) => a.fechaCierre.localeCompare(b.fechaCierre)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [convocatorias, anio, mes]
  );
  const abrenEsteMes = useMemo(
    () =>
      convocatorias
        .filter((c) => esProxima(c) && aperturaISO(c) && enMes(aperturaISO(c) as string))
        .sort((a, b) => (aperturaISO(a) as string).localeCompare(aperturaISO(b) as string)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [convocatorias, anio, mes]
  );
  const sinPlazo = useMemo(() => convocatorias.filter((c) => !esProxima(c) && plazoSinFijar(c)).sort((a, b) => b.matchingGlobal - a.matchingGlobal), [convocatorias]);
  const visibles = verTodas ? abiertas : abiertas.slice(0, FILAS_INICIALES);

  const empezarYa = abiertas.filter((c) => c.diasRestantes <= PREPARACION_DIAS).length;
  const dinero = abiertas.reduce((a, c) => a + fondosDe(c), 0);
  // El eje arranca hoy en el mes actual (lo anterior ya pasó) y el día 1 en los demás
  const inicioEje = esMesActual ? hoy.getDate() : 1;
  const pct = (dia: number) => `${Math.max(0, Math.min(100, ((dia - inicioEje + 0.5) / (diasMes - inicioEje + 1)) * 100))}%`;
  const marcaHoy = esMesActual && <span className="absolute inset-y-0 w-px bg-zinc-400/70 pointer-events-none" style={{ left: pct(hoy.getDate()) }} />;
  const campo = 'appearance-none text-center px-5 py-2 border border-zinc-200 bg-white text-sm font-semibold capitalize text-zinc-800 focus:outline-hidden focus:border-zinc-500 rounded-full';

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-wrap gap-x-10 gap-y-2">
          <div>
            <span className="font-serif text-3xl font-bold text-zinc-900">{abiertas.length}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">Cierran en {nombreMes(mes)}</span>
            <span className="block text-xs text-zinc-500">convocatorias abiertas</span>
          </div>
          <div>
            <span className="font-serif text-3xl font-bold text-rose-600">{empezarYa}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">Hay que empezar ya</span>
            <span className="block text-xs text-zinc-500">cierran en {PREPARACION_DIAS} días o menos</span>
          </div>
          <div>
            <span className="font-serif text-3xl font-bold text-zinc-900">{formatoEuros(dinero)}</span>
            <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">En juego</span>
            <span className="block text-xs text-zinc-500">importe máximo de las que cierran</span>
          </div>
        </div>

        {/* Selector de mes y año */}
        <div className="flex items-center gap-2">
          <button onClick={() => mover(-1)} aria-label="Mes anterior" className="h-9 w-9 rounded-full border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50">‹</button>
          <select value={mes} onChange={(e) => { setMes(Number(e.target.value)); setVerTodas(false); }} className={campo} aria-label="Mes">
            {Array.from({ length: 12 }, (_, m) => <option key={m} value={m}>{nombreMes(m)}</option>)}
          </select>
          <select value={anio} onChange={(e) => { setAnio(Number(e.target.value)); setVerTodas(false); }} className={campo} aria-label="Año">
            {[hoy.getFullYear() - 1, hoy.getFullYear(), hoy.getFullYear() + 1, hoy.getFullYear() + 2].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
          <button onClick={() => mover(1)} aria-label="Mes siguiente" className="h-9 w-9 rounded-full border border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50">›</button>
          {!esMesActual && (
            <button onClick={() => { setAnio(hoy.getFullYear()); setMes(hoy.getMonth()); setVerTodas(false); }} className="ml-1 text-xs font-semibold uppercase tracking-wide text-zinc-600 underline hover:text-zinc-900">Este mes</button>
          )}
        </div>
      </div>

      {abrenEsteMes.length > 0 && (
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-l-2 border-sky-500 bg-sky-50 px-3 py-2 text-xs text-sky-900">
          <strong className="uppercase tracking-wide">Abren en {nombreMes(mes)}</strong>
          {abrenEsteMes.map((c) => (
            <button key={c.id} onClick={() => onSeleccionar(c)} className="text-left hover:underline">
              <strong>{diaDe(aperturaISO(c) as string)} {nombreMes(mes).slice(0, 3)}</strong> · {c.titulo.length > 70 ? `${c.titulo.slice(0, 70)}…` : c.titulo}
            </button>
          ))}
        </p>
      )}

      <div className="border border-zinc-200 bg-white overflow-x-auto">
        <div className="min-w-[940px]">
          <div className="border-b border-zinc-200 bg-zinc-50 p-3">
            <span className="block text-xs font-bold uppercase tracking-[0.15em] text-brand">Cierres de {nombreMes(mes)} {anio}</span>
            <span className="block text-[11px] text-zinc-500">{abiertas.length > 0 ? `${abiertas.length} ${abiertas.length === 1 ? 'convocatoria abierta cierra' : 'convocatorias abiertas cierran'} este mes` : 'Ninguna convocatoria abierta cierra este mes'}</span>
          </div>

          {visibles.map((c) => {
            const cierre = diaDe(c.fechaCierre);
            const inicio = inicioEje;
            const inicioPrep = Math.max(inicio, cierre - PREPARACION_DIAS);
            return (
              <button key={c.id} onClick={() => onSeleccionar(c)} className={`w-full grid grid-cols-[360px_1fr] border-b border-zinc-100 text-left hover:bg-zinc-50 group ${!c.elegible ? 'bg-zinc-50' : ''}`}>
                <Descripcion c={c} />
                <div className="relative">
                  {marcaHoy}
                  {inicioPrep > inicio && <span className="absolute top-1/2 -translate-y-1/2 h-2 bg-emerald-100" style={{ left: pct(inicio), width: `calc(${pct(inicioPrep)} - ${pct(inicio)})` }} />}
                  <span className={`absolute top-1/2 -translate-y-1/2 h-4 ${colorBarra(c.diasRestantes)}`} style={{ left: pct(inicioPrep), width: `calc(${pct(cierre)} - ${pct(inicioPrep)})`, minWidth: 6 }} />
                  <span className="absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 -translate-x-1/2 rotate-45 bg-zinc-900" style={{ left: pct(cierre) }} />
                  <span
                    className="absolute top-1/2 -translate-y-1/2 text-xs font-semibold text-zinc-700 whitespace-nowrap"
                    style={(cierre - inicioEje) / (diasMes - inicioEje + 1) > 0.7 ? { right: `calc(100% - ${pct(cierre)} + 14px)` } : { left: `calc(${pct(cierre)} + 14px)` }}
                  >
                    cierra {fechaCorta(c.fechaCierre.slice(0, 10))} · {c.diasRestantes} d
                  </span>
                </div>
              </button>
            );
          })}
          {abiertas.length === 0 && (
            <p className="p-6 text-center text-sm text-zinc-400">
              {anio < hoy.getFullYear() || (anio === hoy.getFullYear() && mes < hoy.getMonth()) ? 'Este mes ya ha pasado.' : 'Sin cierres este mes con los filtros actuales.'}
            </p>
          )}
        </div>
      </div>

      {abiertas.length > FILAS_INICIALES && (
        <button onClick={() => setVerTodas((v) => !v)} className="rounded-full border border-zinc-300 px-6 py-3 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
          {verTodas ? 'Ver menos' : `Ver las ${abiertas.length - FILAS_INICIALES} restantes`}
        </button>
      )}

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-zinc-500">
        <span className="flex items-center gap-2"><span className="h-2 w-6 bg-emerald-100" /> margen para decidir</span>
        <span className="flex items-center gap-2"><span className="h-4 w-6 bg-brand" /> preparación estimada ({PREPARACION_DIAS} d) · rojo si quedan menos de 7 d, ámbar menos de 20 d</span>
        <span className="flex items-center gap-2"><span className="h-3 w-3 rotate-45 bg-zinc-900" /> cierre</span>
        {esMesActual && <span className="flex items-center gap-2"><span className="h-4 w-px bg-zinc-400" /> hoy</span>}
      </div>

      {sinPlazo.length > 0 && (
        <div>
          <button onClick={() => setVerSinPlazo((v) => !v)} className="text-xs text-zinc-500 underline hover:text-zinc-900">
            {verSinPlazo ? 'Ocultar' : 'Ver'} {sinPlazo.length} abiertas sin plazo de cierre publicado
          </button>
          {verSinPlazo && (
            <ul className="mt-2 divide-y divide-zinc-200 border border-zinc-200 bg-white">
              {sinPlazo.map((c) => (
                <li key={c.id}>
                  <button onClick={() => onSeleccionar(c)} className="w-full text-left flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-50">
                    <span className="min-w-0">
                      <span className="block text-xs text-zinc-500 truncate">{c.organismo}</span>
                      <span className="text-sm font-semibold text-zinc-900 line-clamp-1">{c.titulo}</span>
                    </span>
                    <span className="shrink-0 text-right text-xs text-zinc-600">
                      <strong className="block text-sm text-zinc-900">{textoImporte(c)}</strong>
                      encaje {c.matchingGlobal}%
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
