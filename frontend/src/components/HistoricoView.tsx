'use client';

import React, { useMemo, useState } from 'react';
import { Search, History, CalendarClock, AlertTriangle } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { COMUNIDADES, ESTATAL, TODOS, filtrarPorTerritorio, formatoEuros } from '@/lib/territorio';
import { Confianza, Programa, detectarProgramas, nombreMes, previstosEn } from '@/lib/recurrencia';

interface HistoricoViewProps {
  /** Activas + cerradas (2020 en adelante) */
  historico: Convocatoria[];
  /** null = cargando; false = el backend no responde */
  disponible: boolean | null;
  onSeleccionar: (c: Convocatoria) => void;
}

const POR_PAGINA = 30;
const anioDe = (c: Convocatoria) => Number(c.fechaPublicacion.slice(0, 4));
const fechaLarga = (d: Date) => d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
const mesAnio = (d: Date) => `${nombreMes(d.getMonth() + 1)} ${d.getFullYear()}`;

const BADGE_CONFIANZA: Record<Confianza, string> = {
  alta: 'bg-brand text-white',
  media: 'bg-amber-100 text-amber-800',
  baja: 'bg-zinc-100 text-zinc-600',
};

const campo = 'px-3 py-2 border border-zinc-200 bg-white text-sm text-zinc-800 focus:outline-hidden focus:border-zinc-500';

function Aviso({ children }: { children: React.ReactNode }) {
  return <div className="border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500">{children}</div>;
}

/** Búsqueda dinámica en el histórico: filtros combinables, distribución por año y resultados paginados. */
function Buscador({ historico, onSeleccionar }: { historico: Convocatoria[]; onSeleccionar: (c: Convocatoria) => void }) {
  const [q, setQ] = useState('');
  const [desde, setDesde] = useState(0);
  const [hasta, setHasta] = useState(0);
  const [territorio, setTerritorio] = useState(TODOS);
  const [estado, setEstado] = useState<'todas' | 'abiertas' | 'cerradas'>('todas');
  const [soloAptas, setSoloAptas] = useState(false);
  const [orden, setOrden] = useState<'reciente' | 'cuantia' | 'encaje'>('reciente');
  const [visibles, setVisibles] = useState(POR_PAGINA);

  const anios = useMemo(() => {
    const ys = historico.map(anioDe).filter((y) => y > 1990);
    return ys.length ? Array.from({ length: Math.max(...ys) - Math.min(...ys) + 1 }, (_, i) => Math.min(...ys) + i) : [];
  }, [historico]);

  // Todo menos el rango de años: con esto se dibuja la distribución por año
  const sinRango = useMemo(() => {
    const t = q.trim().toLowerCase();
    const base = historico.filter((c) => {
      if (t && !`${c.titulo} ${c.organismo} ${c.codigoOficial} ${c.resumenEjecutivo}`.toLowerCase().includes(t)) return false;
      if (soloAptas && !c.elegible) return false;
      if (estado === 'abiertas' && c.estado === 'CERRADA') return false;
      if (estado === 'cerradas' && c.estado !== 'CERRADA') return false;
      return true;
    });
    return filtrarPorTerritorio(base, territorio);
  }, [historico, q, soloAptas, estado, territorio]);

  const resultados = useMemo(() => {
    const r = sinRango.filter((c) => (!desde || anioDe(c) >= desde) && (!hasta || anioDe(c) <= hasta));
    return r.sort((a, b) =>
      orden === 'cuantia' ? b.cuantiaMaximaProyecto - a.cuantiaMaximaProyecto : orden === 'encaje' ? b.matchingGlobal - a.matchingGlobal : b.fechaPublicacion.localeCompare(a.fechaPublicacion)
    );
  }, [sinRango, desde, hasta, orden]);

  const porAnio = useMemo(() => {
    const m = new Map<number, number>();
    sinRango.forEach((c) => m.set(anioDe(c), (m.get(anioDe(c)) ?? 0) + 1));
    return m;
  }, [sinRango]);
  const maxAnio = Math.max(1, ...porAnio.values());
  const total = resultados.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const reset = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setVisibles(POR_PAGINA);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <input
            value={q}
            onChange={(e) => reset(setQ)(e.target.value)}
            placeholder="Buscar por título, organismo, código o tema…"
            className={`${campo} w-full pl-9`}
          />
        </div>
        <select className={campo} value={territorio} onChange={(e) => reset(setTerritorio)(e.target.value)}>
          <option value={TODOS}>Todo el territorio</option>
          <option value={ESTATAL}>Ámbito estatal</option>
          {COMUNIDADES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className={campo} value={desde} onChange={(e) => reset(setDesde)(Number(e.target.value))} aria-label="Desde el año">
          <option value={0}>Desde…</option>
          {anios.map((y) => <option key={y}>{y}</option>)}
        </select>
        <select className={campo} value={hasta} onChange={(e) => reset(setHasta)(Number(e.target.value))} aria-label="Hasta el año">
          <option value={0}>Hasta…</option>
          {anios.map((y) => <option key={y}>{y}</option>)}
        </select>
        <select className={campo} value={estado} onChange={(e) => reset(setEstado)(e.target.value as typeof estado)}>
          <option value="todas">Abiertas y cerradas</option>
          <option value="abiertas">Solo abiertas</option>
          <option value="cerradas">Solo cerradas</option>
        </select>
        <button
          onClick={() => reset(setSoloAptas)(!soloAptas)}
          className={`px-4 py-2 border text-xs font-semibold uppercase tracking-wide ${soloAptas ? 'bg-brand border-brand text-white' : 'bg-white border-zinc-200 text-zinc-600'}`}
        >
          Solo aptas
        </button>
        <select className={campo} value={orden} onChange={(e) => setOrden(e.target.value as typeof orden)}>
          <option value="reciente">Más recientes</option>
          <option value="cuantia">Mayor cuantía</option>
          <option value="encaje">Mayor encaje</option>
        </select>
      </div>

      {/* Distribución por año: pulsar una barra filtra ese año */}
      {anios.length > 1 && (
        <div className="flex items-end gap-2 border border-zinc-200 bg-white px-4 pt-3 pb-2">
          {anios.map((y) => {
            const n = porAnio.get(y) ?? 0;
            const activo = desde === y && hasta === y;
            return (
              <button
                key={y}
                onClick={() => {
                  setDesde(activo ? 0 : y);
                  setHasta(activo ? 0 : y);
                  setVisibles(POR_PAGINA);
                }}
                className="group flex-1 flex flex-col items-center gap-1 text-xs text-zinc-500"
                title={`${n} convocatorias en ${y}`}
              >
                <span className="font-semibold text-zinc-700">{n}</span>
                <span className="w-full h-14 flex items-end">
                  <span className={`w-full transition-colors ${activo ? 'bg-zinc-900' : 'bg-brand/70 group-hover:bg-brand'}`} style={{ height: `${Math.max(4, (n / maxAnio) * 100)}%` }} />
                </span>
                <span className={activo ? 'font-bold text-zinc-900' : ''}>{y}</span>
              </button>
            );
          })}
        </div>
      )}

      <p className="text-sm text-zinc-500">
        <strong className="text-zinc-900">{resultados.length}</strong> resultados · {formatoEuros(total)} en cuantías máximas
      </p>

      <ul className="divide-y divide-zinc-200 border border-zinc-200 bg-white">
        {resultados.slice(0, visibles).map((c) => (
          <li key={c.id}>
            <button onClick={() => onSeleccionar(c)} className="w-full text-left grid grid-cols-[88px_1fr_auto] md:grid-cols-[88px_1fr_130px_70px] items-center gap-4 px-4 py-3 hover:bg-zinc-50">
              <span className="text-xs text-zinc-500">
                <span className="block font-semibold text-zinc-800">{new Date(`${c.fechaPublicacion}T12:00:00`).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' })}</span>
                <span className={c.estado === 'CERRADA' ? 'text-zinc-400' : 'font-semibold text-brand'}>{c.estado === 'CERRADA' ? 'cerrada' : 'abierta'}</span>
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold leading-snug text-zinc-900 line-clamp-2">{c.titulo}</span>
                <span className="block text-xs text-zinc-500 truncate">{c.organismo} · {c.ambitoTerritorial}</span>
              </span>
              <span className="hidden md:block text-right text-sm text-zinc-700">{formatoEuros(c.cuantiaMaximaProyecto)}</span>
              <span className={`text-right font-serif text-lg font-bold ${c.elegible ? 'text-zinc-900' : 'text-rose-600'}`}>{c.matchingGlobal}%</span>
            </button>
          </li>
        ))}
        {resultados.length === 0 && <li className="p-8 text-center text-sm text-zinc-400">Nada con esos filtros.</li>}
      </ul>
      {resultados.length > visibles && (
        <button onClick={() => setVisibles((v) => v + POR_PAGINA)} className="mx-auto block px-6 py-2.5 border border-zinc-300 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
          Mostrar {Math.min(POR_PAGINA, resultados.length - visibles)} más
        </button>
      )}
    </div>
  );
}

function TarjetaPrograma({ p, onSeleccionar }: { p: Programa; onSeleccionar: (c: Convocatoria) => void }) {
  return (
    <article className="border border-zinc-200 bg-white p-4 flex flex-col md:flex-row gap-4 md:gap-6">
      <div className="md:w-44 shrink-0">
        {p.abierta ? (
          <>
            <span className="block text-xs font-semibold uppercase tracking-wide text-brand">Abierta ahora</span>
            <span className="block font-serif text-2xl font-bold text-zinc-900">{p.abierta.diasRestantes >= 9999 ? 'Sin plazo' : `${p.abierta.diasRestantes} días`}</span>
          </>
        ) : (
          <>
            <span className={`block text-xs font-semibold uppercase tracking-wide ${p.retrasada ? 'text-amber-700' : 'text-zinc-500'}`}>
              {p.retrasada ? 'Debería haber salido' : 'Previsto'}
            </span>
            <span className="block font-serif text-2xl font-bold text-zinc-900 capitalize">{mesAnio(p.proxima)}</span>
            {!p.retrasada && <span className="block text-xs text-zinc-500">preparar desde el {fechaLarga(p.prepararDesde)}</span>}
          </>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-zinc-500">{p.organismo} · {p.ambito}</p>
        <h3 className="mt-1 font-serif text-base font-bold leading-snug text-zinc-900 line-clamp-2">{p.nombre}</h3>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-600">
          <span>Suele publicarse en <strong className="text-zinc-900">{nombreMes(p.mesApertura)}</strong></span>
          {p.ventanaDias !== null && <span>Plazo típico ≈ <strong className="text-zinc-900">{p.ventanaDias} días</strong></span>}
          {p.cuantiaMedia > 0 && <span>Cuantía media <strong className="text-zinc-900">{formatoEuros(p.cuantiaMedia)}</strong></span>}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {p.ediciones.slice(0, 6).map((c) => (
            <button key={c.id} onClick={() => onSeleccionar(c)} className="px-2 py-0.5 border border-zinc-200 text-xs text-zinc-700 hover:bg-zinc-900 hover:text-white transition-colors" title={c.titulo}>
              {c.fechaPublicacion.slice(0, 4)}
            </button>
          ))}
        </div>
      </div>
      <div className="md:w-24 md:text-right shrink-0">
        <span className={`inline-block rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wide ${BADGE_CONFIANZA[p.confianza]}`}>Fiabilidad {p.confianza}</span>
        <span className="block mt-1 text-[11px] text-zinc-500">{p.anios.length} años con edición</span>
      </div>
    </article>
  );
}

/** Previsión: qué programas recurrentes volverán a abrirse en los próximos X meses, según el histórico. */
function Prevision({ historico, onSeleccionar }: { historico: Convocatoria[]; onSeleccionar: (c: Convocatoria) => void }) {
  const [meses, setMeses] = useState(6);
  const [soloFiables, setSoloFiables] = useState(false);
  const programas = useMemo(() => detectarProgramas(historico), [historico]);
  const abiertas = programas.filter((p) => p.abierta);
  const previstos = useMemo(
    () => previstosEn(programas, meses).filter((p) => !soloFiables || p.confianza !== 'baja'),
    [programas, meses, soloFiables]
  );
  const retrasados = previstos.filter((p) => p.retrasada);
  const proximos = previstos.filter((p) => !p.retrasada);

  if (programas.length === 0) {
    return (
      <Aviso>
        No hay programas con ediciones en al menos dos años distintos. La previsión necesita el histórico (2020 en adelante) y mejora con cada año cargado.
      </Aviso>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-zinc-600">
          <strong className="text-zinc-900">{programas.length}</strong> programas recurrentes detectados en el histórico.
        </p>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-zinc-500">Horizonte:</span>
          {[3, 6, 12, 24].map((m) => (
            <button key={m} onClick={() => setMeses(m)} className={`px-3 py-1.5 border font-semibold ${meses === m ? 'bg-zinc-900 border-zinc-900 text-white' : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50'}`}>
              {m} meses
            </button>
          ))}
          <button onClick={() => setSoloFiables(!soloFiables)} className={`ml-2 px-3 py-1.5 border font-semibold ${soloFiables ? 'bg-brand border-brand text-white' : 'bg-white border-zinc-200 text-zinc-600'}`}>
            Ocultar poco fiables
          </button>
        </div>
      </div>

      {abiertas.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.15em] text-brand">Ya abiertas · edición de este año en curso</h3>
          <div className="space-y-3">{abiertas.map((p) => <TarjetaPrograma key={p.clave} p={p} onSeleccionar={onSeleccionar} />)}</div>
        </section>
      )}

      {retrasados.length > 0 && (
        <section>
          <h3 className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-amber-700">
            <AlertTriangle className="h-4 w-4" /> Fuera de calendario · no ha salido este año y puede publicarse en cualquier momento
          </h3>
          <div className="space-y-3">{retrasados.map((p) => <TarjetaPrograma key={p.clave} p={p} onSeleccionar={onSeleccionar} />)}</div>
        </section>
      )}

      <section>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.15em] text-zinc-500">Previstas en los próximos {meses} meses</h3>
        {proximos.length === 0 ? (
          <Aviso>Ningún programa recurrente tiene su apertura habitual en los próximos {meses} meses.</Aviso>
        ) : (
          <div className="space-y-3">{proximos.map((p) => <TarjetaPrograma key={p.clave} p={p} onSeleccionar={onSeleccionar} />)}</div>
        )}
      </section>

      <p className="text-xs text-zinc-400 leading-relaxed">
        Cómo se calcula: se agrupan las convocatorias del mismo órgano y título (sin años ni números de orden); si hay ediciones en al menos dos años, el mes habitual es el de publicación más frecuente, y la fiabilidad depende de cuántos años hay y de cuántos caen a ±1 mes. Es una estimación: una convocatoria puede cambiar de fecha o no repetirse.
      </p>
    </div>
  );
}

export function HistoricoView({ historico, disponible, onSeleccionar }: HistoricoViewProps) {
  const [vista, setVista] = useState<'buscar' | 'prevision'>('buscar');

  if (disponible === null) return <Aviso>Cargando el histórico…</Aviso>;
  if (!disponible || historico.length === 0) {
    return (
      <Aviso>
        <History className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
        El histórico viene del backend y ahora mismo no está disponible. Cuando el radar esté conectado aparecerán aquí las convocatorias desde 2020 y la previsión de recurrencia.
      </Aviso>
    );
  }

  const anios = historico.map(anioDe).filter((y) => y > 1990);
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex border border-zinc-200 bg-white text-xs font-semibold uppercase tracking-wide">
          {([['buscar', 'Buscar', Search], ['prevision', 'Previsión', CalendarClock]] as const).map(([id, etiqueta, Icono]) => (
            <button key={id} onClick={() => setVista(id)} className={`flex items-center gap-2 px-4 py-2 transition-colors ${vista === id ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-50'}`}>
              <Icono className="h-3.5 w-3.5" /> {etiqueta}
            </button>
          ))}
        </div>
        <p className="text-xs text-zinc-500">
          {historico.length} convocatorias · {Math.min(...anios)}–{Math.max(...anios)}
        </p>
      </div>
      {vista === 'buscar' ? <Buscador historico={historico} onSeleccionar={onSeleccionar} /> : <Prevision historico={historico} onSeleccionar={onSeleccionar} />}
    </div>
  );
}
