'use client';

import React, { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';

interface CalendarViewProps {
  convocatorias: Convocatoria[];
  onSeleccionar: (convocatoria: Convocatoria) => void;
}

const DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

const clave = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

const colorUrgencia = (dias: number) =>
  dias < 7 ? 'border-rose-500 bg-rose-50 text-rose-900' : dias < 20 ? 'border-amber-500 bg-amber-50 text-amber-900' : 'border-brand bg-emerald-50 text-emerald-900';

const corto = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)}k €` : `${n} €`);

/** Vista mensual clásica. */
function MesCalendario({ convocatorias, onSeleccionar }: CalendarViewProps) {
  const hoy = useMemo(() => new Date(), []);
  const [mes, setMes] = useState(() => new Date(hoy.getFullYear(), hoy.getMonth(), 1));
  const [seleccionado, setSeleccionado] = useState<string | null>(null);

  const porDia = useMemo(() => {
    const m = new Map<string, Convocatoria[]>();
    convocatorias.forEach((c) => m.set(c.fechaCierre, [...(m.get(c.fechaCierre) ?? []), c]));
    m.forEach((lista) => lista.sort((a, b) => b.matchingGlobal - a.matchingGlobal));
    return m;
  }, [convocatorias]);

  // Rejilla: semanas completas que cubren el mes (lunes primero)
  const celdas = useMemo(() => {
    const primero = new Date(mes.getFullYear(), mes.getMonth(), 1);
    const offset = (primero.getDay() + 6) % 7;
    const ultimo = new Date(mes.getFullYear(), mes.getMonth() + 1, 0);
    const total = Math.ceil((offset + ultimo.getDate()) / 7) * 7;
    return Array.from({ length: total }, (_, i) => new Date(mes.getFullYear(), mes.getMonth(), 1 - offset + i));
  }, [mes]);

  const delMes = convocatorias.filter((c) => c.fechaCierre.startsWith(`${mes.getFullYear()}-${String(mes.getMonth() + 1).padStart(2, '0')}`));
  const importeMes = delMes.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);

  const hoyClave = clave(hoy);
  const proximos = [...convocatorias]
    .filter((c) => c.fechaCierre >= hoyClave)
    .sort((a, b) => a.fechaCierre.localeCompare(b.fechaCierre))
    .slice(0, 6);
  const detalle = seleccionado ? porDia.get(seleccionado) ?? [] : proximos;

  const mover = (delta: number) => {
    setMes((m) => new Date(m.getFullYear(), m.getMonth() + delta, 1));
    setSeleccionado(null);
  };

  const tituloMes = mes.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
  const titulo = tituloMes.charAt(0).toUpperCase() + tituloMes.slice(1);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <div className="lg:col-span-8">
        {/* Cabecera del mes */}
        <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
          <div>
            <h2 className="font-serif text-3xl font-bold text-zinc-900">{titulo}</h2>
            <p className="text-sm text-zinc-500">
              {delMes.length} {delMes.length === 1 ? 'cierre' : 'cierres'} · {formatoEuros(importeMes)} en juego
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => mover(-1)} aria-label="Mes anterior" className="h-10 w-10 rounded-full border border-zinc-300 flex items-center justify-center hover:bg-zinc-100">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => { setMes(new Date(hoy.getFullYear(), hoy.getMonth(), 1)); setSeleccionado(null); }}
              className="h-10 px-5 rounded-full border border-zinc-300 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-100"
            >
              Hoy
            </button>
            <button onClick={() => mover(1)} aria-label="Mes siguiente" className="h-10 w-10 rounded-full border border-zinc-300 flex items-center justify-center hover:bg-zinc-100">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Rejilla */}
        <div className="border-l border-t border-zinc-200 bg-white">
          <div className="grid grid-cols-7">
            {DIAS_SEMANA.map((d) => (
              <div key={d} className="border-r border-b border-zinc-200 bg-zinc-50 px-2 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                {d}
              </div>
            ))}
            {celdas.map((dia) => {
              const k = clave(dia);
              const eventos = porDia.get(k) ?? [];
              const delMesActual = dia.getMonth() === mes.getMonth();
              const esHoy = k === hoyClave;
              const activo = seleccionado === k;
              return (
                <div
                  key={k}
                  onClick={() => eventos.length && setSeleccionado(activo ? null : k)}
                  className={`min-h-[104px] border-r border-b border-zinc-200 p-1.5 flex flex-col gap-1 transition-colors ${
                    delMesActual ? 'bg-white' : 'bg-zinc-50/70'
                  } ${eventos.length ? 'cursor-pointer hover:bg-zinc-50' : ''} ${activo ? 'ring-2 ring-inset ring-zinc-900' : ''}`}
                >
                  <span
                    className={`self-end text-xs font-semibold h-6 w-6 flex items-center justify-center rounded-full ${
                      esHoy ? 'bg-zinc-900 text-white' : delMesActual ? 'text-zinc-700' : 'text-zinc-300'
                    }`}
                  >
                    {dia.getDate()}
                  </span>
                  {eventos.slice(0, 2).map((c) => (
                    <button
                      key={c.id}
                      onClick={(e) => { e.stopPropagation(); onSeleccionar(c); }}
                      title={c.titulo}
                      className={`w-full text-left truncate border-l-[3px] px-1.5 py-0.5 text-[11px] leading-tight font-medium ${colorUrgencia(c.diasRestantes)}`}
                    >
                      {corto(c.cuantiaMaximaProyecto)} · {c.ambitoTerritorial}
                    </button>
                  ))}
                  {eventos.length > 2 && <span className="text-[11px] font-semibold text-zinc-500 px-1">+{eventos.length - 2} más</span>}
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 bg-rose-500" /> menos de 7 días</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 bg-amber-500" /> menos de 20 días</span>
          <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 bg-brand" /> más de 20 días</span>
        </div>
      </div>

      {/* Detalle: día elegido o próximos cierres */}
      <aside className="lg:col-span-4 space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-brand">{seleccionado ? 'Cierran este día' : 'Próximos cierres'}</p>
          <h3 className="mt-1 font-serif text-xl font-bold text-zinc-900">
            {seleccionado
              ? new Date(`${seleccionado}T12:00:00`).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })
              : 'Lo que vence antes'}
          </h3>
        </div>
        <ul className="divide-y divide-zinc-200 border-y border-zinc-200">
          {detalle.map((c) => (
            <li key={c.id}>
              <button onClick={() => onSeleccionar(c)} className="w-full text-left py-4 flex gap-4 hover:bg-zinc-50">
                <span className={`shrink-0 w-14 text-center border-l-[3px] pl-2 ${colorUrgencia(c.diasRestantes)} bg-transparent`}>
                  <span className="block font-serif text-2xl font-bold leading-none">{c.diasRestantes}</span>
                  <span className="block text-[11px] uppercase">días</span>
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-zinc-900 line-clamp-2">{c.titulo}</span>
                  <span className="mt-1 block text-xs text-zinc-500">
                    {formatoEuros(c.cuantiaMaximaProyecto)} · encaje {c.matchingGlobal}% · cierra {new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                  </span>
                </span>
              </button>
            </li>
          ))}
          {detalle.length === 0 && <li className="py-6 text-sm text-zinc-400">No hay cierres con los filtros actuales.</li>}
        </ul>
      </aside>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Línea de tiempo: plan de ataque. Todo legible sin pulsar.
// ---------------------------------------------------------------------------

/** Días de preparación estimados de una solicitud (supuesto de trabajo, editable). */
const PREPARACION_DIAS = 14;

const colorBarra = (dias: number) => (dias < 7 ? 'bg-rose-500' : dias < 20 ? 'bg-amber-500' : 'bg-brand');

function LineaTiempo({ convocatorias, onSeleccionar }: CalendarViewProps) {
  const [rango, setRango] = useState<30 | 60 | 90>(60);
  const [verTodas, setVerTodas] = useState(false);
  const hoy = useMemo(() => new Date(), []);

  const filas = useMemo(
    () => convocatorias.filter((c) => c.diasRestantes >= 0 && c.diasRestantes <= rango).sort((a, b) => a.diasRestantes - b.diasRestantes),
    [convocatorias, rango]
  );
  const visibles = verTodas ? filas : filas.slice(0, 12);

  const semanas = Math.ceil(rango / 7);
  const porSemana = Array.from({ length: semanas }, (_, i) => filas.filter((c) => Math.floor(c.diasRestantes / 7) === i));
  const maxSemana = Math.max(1, ...porSemana.map((l) => l.length));
  const semanaCarga = porSemana.reduce((mejor, l, i) => (l.length > porSemana[mejor].length ? i : mejor), 0);
  const empezarYa = filas.filter((c) => c.diasRestantes <= PREPARACION_DIAS).length;
  const en7 = filas.filter((c) => c.diasRestantes <= 7).length;

  const fechaSemana = (i: number) => {
    const d = new Date(hoy);
    d.setDate(d.getDate() + i * 7);
    return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  };
  const pct = (dias: number) => `${Math.min(100, (dias / rango) * 100)}%`;

  return (
    <div className="space-y-6">
      {/* Lectura rápida */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-zinc-200 border border-zinc-200">
        <div className="bg-white p-5">
          <span className="font-serif text-4xl font-bold text-rose-600">{empezarYa}</span>
          <span className="block mt-1 text-sm font-bold uppercase tracking-wide text-zinc-900">Hay que empezar ya</span>
          <span className="block text-sm text-zinc-500">quedan {PREPARACION_DIAS} días o menos: no da tiempo a esperar</span>
        </div>
        <div className="bg-white p-5">
          <span className="font-serif text-4xl font-bold text-zinc-900">{en7}</span>
          <span className="block mt-1 text-sm font-bold uppercase tracking-wide text-zinc-900">Cierran esta semana</span>
          <span className="block text-sm text-zinc-500">en los próximos 7 días</span>
        </div>
        <div className="bg-white p-5">
          <span className="font-serif text-4xl font-bold text-zinc-900">{porSemana[semanaCarga]?.length ?? 0}</span>
          <span className="block mt-1 text-sm font-bold uppercase tracking-wide text-zinc-900">Semana más cargada</span>
          <span className="block text-sm text-zinc-500">cierres a partir del {fechaSemana(semanaCarga)}</span>
        </div>
      </div>

      {/* Rango */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <p className="text-sm text-zinc-500">
          <strong className="text-zinc-900">{filas.length}</strong> convocatorias en los próximos {rango} días, ordenadas por fecha de cierre
        </p>
        <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1">
          {([30, 60, 90] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRango(r)}
              className={`px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-wide transition-colors ${rango === r ? 'bg-[#333] text-white' : 'text-zinc-600 hover:text-zinc-900'}`}
            >
              {r} días
            </button>
          ))}
        </div>
      </div>

      {/* Cronograma */}
      <div className="border border-zinc-200 bg-white overflow-x-auto">
        <div className="min-w-[860px]">
          {/* Eje de semanas y carga */}
          <div className="grid grid-cols-[300px_1fr] border-b border-zinc-200 bg-zinc-50">
            <div className="p-3 text-xs font-semibold uppercase tracking-wide text-zinc-500 self-end">Cierres por semana</div>
            <div className="relative h-20">
              <div className="absolute inset-0 grid" style={{ gridTemplateColumns: `repeat(${semanas}, 1fr)` }}>
                {porSemana.map((l, i) => (
                  <div key={i} className="relative border-l border-zinc-200 flex flex-col justify-end items-center pb-6 px-1">
                    {l.length > 0 && (
                      <>
                        <span className="text-xs font-bold text-zinc-700">{l.length}</span>
                        <span className={`w-full max-w-[28px] ${i === semanaCarga ? 'bg-zinc-900' : 'bg-zinc-300'}`} style={{ height: `${(l.length / maxSemana) * 32}px` }} />
                      </>
                    )}
                    <span className="absolute bottom-1 left-1.5 text-[11px] text-zinc-500">{fechaSemana(i)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Filas */}
          {visibles.map((c) => {
            const inicioPrep = Math.max(0, c.diasRestantes - PREPARACION_DIAS);
            const urgente = c.diasRestantes <= PREPARACION_DIAS;
            return (
              <button
                key={c.id}
                onClick={() => onSeleccionar(c)}
                className="w-full grid grid-cols-[300px_1fr] border-b border-zinc-100 text-left hover:bg-zinc-50 group"
              >
                <div className="p-3 pr-4 min-w-0">
                  <span className="block text-sm font-semibold text-zinc-900 leading-snug line-clamp-2 group-hover:text-emerald-800">{c.titulo}</span>
                  <span className="mt-0.5 block text-xs text-zinc-500 truncate">
                    {formatoEuros(c.cuantiaMaximaProyecto)} · encaje {c.matchingGlobal}%
                    {urgente && <span className="ml-2 font-bold text-rose-600">EMPEZAR YA</span>}
                  </span>
                </div>
                <div className="relative">
                  <div className="absolute inset-0 grid pointer-events-none" style={{ gridTemplateColumns: `repeat(${semanas}, 1fr)` }}>
                    {porSemana.map((_, i) => (
                      <div key={i} className="border-l border-zinc-100" />
                    ))}
                  </div>
                  {/* Margen para decidir */}
                  {inicioPrep > 0 && (
                    <span className="absolute top-1/2 -translate-y-1/2 h-2 bg-emerald-100" style={{ left: 0, width: pct(inicioPrep) }} />
                  )}
                  {/* Preparación */}
                  <span
                    className={`absolute top-1/2 -translate-y-1/2 h-4 ${colorBarra(c.diasRestantes)}`}
                    style={{ left: pct(inicioPrep), width: `calc(${pct(c.diasRestantes)} - ${pct(inicioPrep)})`, minWidth: 6 }}
                  />
                  {/* Cierre */}
                  <span
                    className="absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 -translate-x-1/2 rotate-45 bg-zinc-900"
                    style={{ left: pct(c.diasRestantes) }}
                  />
                  <span
                    className="absolute top-1/2 -translate-y-1/2 text-xs font-semibold text-zinc-700 whitespace-nowrap"
                    style={c.diasRestantes / rango > 0.8 ? { right: `calc(${100 - Math.min(100, (c.diasRestantes / rango) * 100)}% + 14px)` } : { left: `calc(${pct(c.diasRestantes)} + 14px)` }}
                  >
                    {new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} · {c.diasRestantes} d
                  </span>
                </div>
              </button>
            );
          })}
          {filas.length === 0 && <p className="p-8 text-center text-sm text-zinc-400">No hay cierres en este rango con los filtros actuales.</p>}
        </div>
      </div>

      {filas.length > 12 && (
        <button onClick={() => setVerTodas((v) => !v)} className="rounded-full border border-zinc-300 px-6 py-3 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
          {verTodas ? 'Ver menos' : `Ver las ${filas.length - 12} restantes`}
        </button>
      )}

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-zinc-500">
        <span className="flex items-center gap-2"><span className="h-2 w-6 bg-emerald-100" /> margen para decidir</span>
        <span className="flex items-center gap-2"><span className="h-4 w-6 bg-brand" /> preparación estimada ({PREPARACION_DIAS} d) · rojo si quedan menos de 7 d, ámbar menos de 20 d</span>
        <span className="flex items-center gap-2"><span className="h-3 w-3 rotate-45 bg-zinc-900" /> cierre</span>
      </div>
    </div>
  );
}

/** Sección «¿Cuándo?»: plan de ataque en línea de tiempo, o vista mensual. */
export function CalendarView(props: CalendarViewProps) {
  const [modo, setModo] = useState<'linea' | 'mes'>('linea');
  return (
    <div className="space-y-6">
      <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1">
        {([['linea', 'Plan de ataque'], ['mes', 'Mes']] as const).map(([id, etiqueta]) => (
          <button
            key={id}
            onClick={() => setModo(id)}
            className={`px-5 py-2 rounded-full text-xs font-semibold uppercase tracking-wide transition-colors ${modo === id ? 'bg-[#333] text-white' : 'text-zinc-600 hover:text-zinc-900'}`}
          >
            {etiqueta}
          </button>
        ))}
      </div>
      {modo === 'linea' ? <LineaTiempo {...props} /> : <MesCalendario {...props} />}
    </div>
  );
}
