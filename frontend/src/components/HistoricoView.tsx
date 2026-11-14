'use client';

import React, { useMemo, useState } from 'react';
import { Search, History } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { COMUNIDADES, ESTATAL, TODOS, filtrarPorTerritorio, formatoImporte } from '@/lib/territorio';
import { puntajeBusqueda } from '@/lib/search';

interface HistoricoViewProps {
  /** Activas + cerradas (2016 en adelante): aquí solo se usan las cerradas */
  historico: Convocatoria[];
  /** null = cargando; false = el backend no responde */
  disponible: boolean | null;
  onSeleccionar: (c: Convocatoria) => void;
}

const POR_PAGINA = 40;
const anioDe = (c: Convocatoria) => c.anio ?? Number(c.fechaPublicacion.slice(0, 4));
const FUENTES: [string, string][] = [
  ['todas', 'Todas'],
  ['publica_estatal', 'Estatal'],
  ['publica_autonomica', 'Autonómica y local'],
  ['europea', 'Europea'],
  ['privada_rsc', 'Empresas'],
];
const campo = 'px-3 py-2 border border-zinc-200 bg-white text-sm text-zinc-800 focus:outline-hidden focus:border-zinc-500';

/** Archivo de convocatorias ya cerradas: se busca por texto, territorio, fuente y año (pulsando la barra del gráfico). */
export function HistoricoView({ historico, disponible, onSeleccionar }: HistoricoViewProps) {
  const [q, setQ] = useState('');
  const [territorio, setTerritorio] = useState(TODOS);
  const [fuente, setFuente] = useState('todas');
  const [anio, setAnio] = useState(0);
  const [visibles, setVisibles] = useState(POR_PAGINA);

  const cerradas = useMemo(() => historico.filter((c) => c.estado === 'CERRADA' && anioDe(c) >= 2016), [historico]);

  // Sin filtrar por año: con esto se dibuja el gráfico
  const base = useMemo(() => {
    const r = cerradas.filter((c) => {
      if (fuente !== 'todas' && c.tipoFuente !== fuente) return false;
      return !q.trim() || puntajeBusqueda(c, q) > 0;
    });
    return filtrarPorTerritorio(r, territorio);
  }, [cerradas, q, fuente, territorio]);

  const resultados = useMemo(
    () => base.filter((c) => !anio || anioDe(c) === anio).sort((a, b) => b.fechaPublicacion.localeCompare(a.fechaPublicacion)),
    [base, anio]
  );
  const porAnio = useMemo(() => {
    const m = new Map<number, number>();
    base.forEach((c) => m.set(anioDe(c), (m.get(anioDe(c)) ?? 0) + 1));
    return m;
  }, [base]);
  const anios = useMemo(() => [...new Set(cerradas.map(anioDe))].sort((a, b) => a - b), [cerradas]);
  const maxAnio = Math.max(1, ...porAnio.values());

  // Agrupadas por año, para que no haya una columna de fechas repetida
  const grupos = useMemo(() => {
    const g = new Map<number, Convocatoria[]>();
    resultados.slice(0, visibles).forEach((c) => g.set(anioDe(c), [...(g.get(anioDe(c)) ?? []), c]));
    return [...g.entries()];
  }, [resultados, visibles]);

  const cambiar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setVisibles(POR_PAGINA);
  };

  if (disponible === null) return <p className="py-16 text-center text-sm text-zinc-400">Cargando el histórico…</p>;
  if (!disponible || cerradas.length === 0) {
    return (
      <div className="border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500">
        <History className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
        {disponible ? 'Todavía no hay convocatorias cerradas en el histórico.' : 'El histórico viene del backend y ahora mismo no está disponible.'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Año a año */}
      <div className="flex items-end gap-1.5">
        {anios.map((y) => {
          const n = porAnio.get(y) ?? 0;
          const activo = anio === y;
          return (
            <button key={y} onClick={() => cambiar(setAnio)(activo ? 0 : y)} className="group flex-1 flex flex-col items-center gap-1 text-xs text-zinc-500" title={`${n} convocatorias cerradas en ${y}`}>
              <span className={`font-semibold ${activo ? 'text-zinc-900' : 'text-zinc-600'}`}>{n}</span>
              <span className="w-full h-16 flex items-end">
                <span className={`w-full transition-colors ${activo ? 'bg-zinc-900' : 'bg-brand/60 group-hover:bg-brand'}`} style={{ height: `${Math.max(3, (n / maxAnio) * 100)}%` }} />
              </span>
              <span className={activo ? 'font-bold text-zinc-900' : ''}>{y}</span>
            </button>
          );
        })}
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <input value={q} onChange={(e) => cambiar(setQ)(e.target.value)} placeholder="Buscar en el archivo…" className={`${campo} w-full pl-9`} />
        </div>
        <select className={campo} value={territorio} onChange={(e) => cambiar(setTerritorio)(e.target.value)}>
          <option value={TODOS}>Todo el territorio</option>
          <option value={ESTATAL}>Ámbito estatal</option>
          {COMUNIDADES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <div className="inline-flex border border-zinc-200 bg-white text-xs font-semibold uppercase tracking-wide">
          {FUENTES.map(([id, etiqueta]) => (
            <button key={id} onClick={() => cambiar(setFuente)(id)} className={`px-3 py-2 transition-colors ${fuente === id ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-50'}`}>
              {etiqueta}
            </button>
          ))}
        </div>
      </div>

      <p className="text-sm text-zinc-500">
        <strong className="text-zinc-900">{resultados.length}</strong> convocatorias cerradas{anio ? ` en ${anio}` : ''}
        {anio > 0 && <button onClick={() => cambiar(setAnio)(0)} className="ml-2 underline hover:text-zinc-900">quitar año ✕</button>}
      </p>

      {/* Resultados agrupados por año */}
      <div className="space-y-6">
        {grupos.map(([y, items]) => (
          <section key={y}>
            <h3 className="mb-1 flex items-baseline gap-2 border-b border-zinc-200 pb-1">
              <span className="font-serif text-xl font-bold text-zinc-900">{y}</span>
              <span className="text-xs text-zinc-400">{resultados.filter((c) => anioDe(c) === y).length}</span>
            </h3>
            <ul>
              {items.map((c) => (
                <li key={c.id}>
                  <button onClick={() => onSeleccionar(c)} className="w-full text-left grid grid-cols-[1fr_auto] items-baseline gap-6 px-1 py-2 hover:bg-zinc-50">
                    <span className="min-w-0">
                      <span className="text-sm text-zinc-900 line-clamp-1">{c.titulo}</span>
                      <span className="block text-xs text-zinc-500 truncate">{c.organismo}</span>
                    </span>
                    <span className="text-right text-xs text-zinc-500 whitespace-nowrap">
                      <span className="font-semibold text-zinc-800">{formatoImporte(c.cuantiaMaximaProyecto)}</span> · {c.matchingGlobal}%
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
        {resultados.length === 0 && <p className="py-10 text-center text-sm text-zinc-400">Nada con esos filtros.</p>}
      </div>
      {resultados.length > visibles && (
        <button onClick={() => setVisibles((v) => v + POR_PAGINA)} className="mx-auto block px-6 py-2.5 border border-zinc-300 text-xs font-semibold uppercase tracking-wide hover:bg-zinc-900 hover:text-white transition-colors">
          Mostrar {Math.min(POR_PAGINA, resultados.length - visibles)} más
        </button>
      )}
    </div>
  );
}
