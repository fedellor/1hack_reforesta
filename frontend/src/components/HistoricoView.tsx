'use client';

import React, { useMemo, useState } from 'react';
import { Search, History } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { COMUNIDADES, ESTATAL, TODOS, esLicitacion, filtrarPorTerritorio, textoImporte } from '@/lib/territorio';
import { detectarProgramas } from '@/lib/recurrencia';

interface HistoricoViewProps {
  /** Activas + cerradas (2020 en adelante): aquí solo se usan las cerradas */
  historico: Convocatoria[];
  /** null = cargando; false = el backend no responde */
  disponible: boolean | null;
  onSeleccionar: (c: Convocatoria) => void;
}

const POR_PAGINA = 25;
const anioDe = (c: Convocatoria) => Number(c.fechaPublicacion.slice(0, 4));
const fechaCorta = (iso: string) =>
  new Date(`${iso.slice(0, 10)}T12:00:00`).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }).replace('.', '');
type Tipo = 'todos' | 'ayuda' | 'licitacion' | 'europea' | 'privada';
const TIPOS: [Tipo, string][] = [
  ['todos', 'Todos los tipos'],
  ['ayuda', 'Ayudas y subvenciones'],
  ['licitacion', 'Licitaciones'],
  ['europea', 'Programas europeos'],
  ['privada', 'Mecenazgo privado'],
];
const tipoDe = (c: Convocatoria): Tipo => (esLicitacion(c) ? 'licitacion' : c.tipoFuente === 'europea' ? 'europea' : c.tipoFuente === 'privada_rsc' ? 'privada' : 'ayuda');
const campo = 'px-3 py-1.5 border border-[#d9d4c7] bg-white text-sm text-zinc-800 focus:outline-hidden focus:border-zinc-500';

/**
 * Archivo: consulta de convocatorias ya cerradas. A propósito no se parece al resto de la plataforma (que es de acción):
 * aquí se busca y se lee, así que es una tabla sobria sobre fondo de papel, con un solo buscador y dos filtros.
 */
export function HistoricoView({ historico, disponible, onSeleccionar }: HistoricoViewProps) {
  const [q, setQ] = useState('');
  const [territorio, setTerritorio] = useState(TODOS);
  const [anio, setAnio] = useState(0);
  const [tipo, setTipo] = useState<Tipo>('todos');
  const [soloAptas, setSoloAptas] = useState(false);
  const [soloRecurrentes, setSoloRecurrentes] = useState(false);
  const [visibles, setVisibles] = useState(POR_PAGINA);

  const cerradas = useMemo(() => historico.filter((c) => c.estado === 'CERRADA' && anioDe(c) >= 2020), [historico]);
  const anios = useMemo(() => [...new Set(cerradas.map(anioDe))].sort((a, b) => b - a), [cerradas]);

  // Ids de convocatorias que pertenecen a un programa que se repite (≥ 2 años de edición)
  const recurrentes = useMemo(() => new Set(detectarProgramas(historico).flatMap((p) => p.ediciones.map((e) => e.id))), [historico]);

  const resultados = useMemo(() => {
    const t = q.trim().toLowerCase();
    const r = cerradas.filter((c) => (!anio || anioDe(c) === anio) && (tipo === 'todos' || tipoDe(c) === tipo) && (!soloAptas || c.elegible) && (!soloRecurrentes || recurrentes.has(c.id)) && (!t || `${c.titulo} ${c.organismo} ${c.codigoOficial}`.toLowerCase().includes(t)));
    return filtrarPorTerritorio(r, territorio).sort((a, b) => b.fechaPublicacion.localeCompare(a.fechaPublicacion));
  }, [cerradas, q, anio, territorio, tipo, soloAptas, soloRecurrentes, recurrentes]);

  const cambiar = <T,>(set: (v: T) => void) => (v: T) => {
    set(v);
    setVisibles(POR_PAGINA);
  };

  if (disponible === null) return <p className="py-16 text-center text-sm text-zinc-400">Cargando el archivo…</p>;
  if (!disponible || cerradas.length === 0) {
    return (
      <div className="border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500">
        <History className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
        {disponible ? 'Todavía no hay convocatorias cerradas en el archivo.' : 'El archivo viene del backend y ahora mismo no está disponible.'}
      </div>
    );
  }

  return (
    <div className="border border-[#d9d4c7] bg-[#f7f5f0]">
      {/* Buscador */}
      <div className="border-b border-[#d9d4c7] p-5 space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="font-serif text-xl font-bold text-zinc-900">Archivo de convocatorias</h2>
          <span className="text-xs text-zinc-500">{cerradas.length} cerradas desde {anios[anios.length - 1]}</span>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <input
            value={q}
            onChange={(e) => cambiar(setQ)(e.target.value)}
            placeholder="Busca por tema, organismo o código…"
            className={`${campo} w-full pl-9 py-2.5 text-base`}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <select className={campo} value={anio} onChange={(e) => cambiar(setAnio)(Number(e.target.value))} aria-label="Año">
            <option value={0}>Todos los años</option>
            {anios.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
          <select className={campo} value={territorio} onChange={(e) => cambiar(setTerritorio)(e.target.value)} aria-label="Territorio">
            <option value={TODOS}>Todo el territorio</option>
            <option value={ESTATAL}>Ámbito estatal</option>
            {COMUNIDADES.map((c) => <option key={c}>{c}</option>)}
          </select>
          <select className={campo} value={tipo} onChange={(e) => cambiar(setTipo)(e.target.value as Tipo)} aria-label="Tipo">
            {TIPOS.map(([id, etiqueta]) => <option key={id} value={id}>{etiqueta}</option>)}
          </select>
          {([
            [soloAptas, setSoloAptas, 'Solo aptas'],
            [soloRecurrentes, setSoloRecurrentes, 'Se repiten'],
          ] as const).map(([activo, set, etiqueta]) => (
            <button
              key={etiqueta}
              type="button"
              role="switch"
              aria-checked={activo}
              onClick={() => cambiar(set)(!activo)}
              className={`px-3 py-1.5 border text-sm transition-colors ${activo ? 'border-zinc-900 bg-zinc-900 text-white' : 'border-[#d9d4c7] bg-white text-zinc-700 hover:bg-zinc-50'}`}
            >
              {etiqueta}
            </button>
          ))}
          <span className="ml-auto text-zinc-500">
            <strong className="text-zinc-900">{resultados.length}</strong> {resultados.length === 1 ? 'resultado' : 'resultados'}
          </span>
        </div>
      </div>

      {/* Tabla */}
      <ul>
        {resultados.slice(0, visibles).map((c) => (
          <li key={c.id} className="border-b border-dotted border-[#cfc9ba] last:border-b-0">
            <button onClick={() => onSeleccionar(c)} className="w-full text-left grid grid-cols-[84px_1fr_auto] items-baseline gap-4 px-5 py-2.5 hover:bg-white/70">
              <span className="text-xs capitalize text-zinc-500 tabular-nums">{fechaCorta(c.fechaPublicacion)}</span>
              <span className="min-w-0">
                <span className="block text-sm text-zinc-900 truncate">{c.titulo}</span>
                <span className="block text-xs text-zinc-500 truncate">{c.organismo}</span>
              </span>
              <span className="text-xs font-semibold text-zinc-700 whitespace-nowrap">{textoImporte(c)}</span>
            </button>
          </li>
        ))}
        {resultados.length === 0 && <li className="p-10 text-center text-sm text-zinc-500">Nada con esos criterios.</li>}
      </ul>

      {resultados.length > visibles && (
        <div className="border-t border-[#d9d4c7] p-4 text-center">
          <button onClick={() => setVisibles((v) => v + POR_PAGINA)} className="text-xs font-semibold uppercase tracking-wide text-zinc-600 underline hover:text-zinc-900">
            Mostrar {Math.min(POR_PAGINA, resultados.length - visibles)} más
          </button>
        </div>
      )}
    </div>
  );
}
