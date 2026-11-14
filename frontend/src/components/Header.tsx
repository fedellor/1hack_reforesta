'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

export interface EstadoDatos {
  fuente: 'cargando' | 'backend' | 'sin_conexion';
  actualizado: Date | null;
}

export type Seccion = 'mapa' | 'plan' | 'historico' | 'empresas' | 'pipeline';

interface HeaderProps {
  convocatorias: Convocatoria[];
  seccion: Seccion;
  setSeccion: (s: Seccion) => void;
  datos: EstadoDatos;
  onRefresh: () => void | Promise<void>;
  /** Convocatorias nuevas desde la última visita (se muestra como contador en el menú) */
  nuevas?: number;
  /** Próxima sincronización automática del backend (ISO) */
  proximaSync?: string | null;
}

const ITEMS_MENU: { id: Seccion; label: string }[] = [
  { id: 'mapa', label: 'Mapa' },
  { id: 'plan', label: 'Plan de ataque' },
  { id: 'historico', label: 'Histórico' },
  { id: 'empresas', label: 'Empresas' },
  { id: 'pipeline', label: 'Pipeline' },
];

export function Header({ convocatorias, seccion, setSeccion, datos, onRefresh, nuevas = 0, proximaSync = null }: HeaderProps) {
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await onRefresh();
    } finally {
      setTimeout(() => setSyncing(false), 600);
    }
  };

  // Tic cada 30 s para que «hace X min» se mantenga al día
  const [ahora, setAhora] = useState(0);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAhora(Date.now());
    const t = setInterval(() => setAhora(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);
  const minutos = datos.actualizado && ahora ? Math.max(0, Math.round((ahora - datos.actualizado.getTime()) / 60000)) : null;
  const etiquetaDatos =
    datos.fuente === 'backend'
      ? `En vivo · ${minutos === null || minutos < 1 ? 'actualizado ahora' : `hace ${minutos} min`}`
      : datos.fuente === 'sin_conexion'
        ? 'Sin conexión con el radar'
        : 'Cargando datos…';

  return (
    <header className="w-full sticky top-0 z-50 shadow-md bg-[#1a1a1a] border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[64px] flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/reforesta/logo-reforesta-verde.png" alt="Reforesta" className="h-[32px] w-auto object-contain" />
          <span className="hidden lg:inline-block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6aa43a] border-l border-white/20 pl-3 py-0.5">
            Radar de financiación
          </span>
        </div>

        <nav className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto min-w-0 shrink-0">
          {ITEMS_MENU.map((item) => {
            const activo = seccion === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setSeccion(item.id)}
                className={`relative px-2.5 sm:px-3.5 py-2 text-[12px] sm:text-[13px] font-semibold uppercase tracking-[0.06em] transition-colors cursor-pointer whitespace-nowrap ${
                  activo ? 'text-[#7cc142]' : 'text-white/90 hover:text-[#7cc142]'
                }`}
              >
                {item.label}
                {item.id === 'plan' && nuevas > 0 && (
                  <span className="ml-1.5 rounded-full bg-[#6aa43a] px-1.5 py-0.5 text-[10px] font-bold text-white align-middle" title="Nuevas desde tu última visita">
                    {nuevas}
                  </span>
                )}
                {activo && <span className="absolute left-2.5 right-2.5 -bottom-[13px] h-[3px] bg-[#6aa43a]" />}
              </button>
            );
          })}
        </nav>

        <div className="hidden md:flex items-center gap-2 text-[11px] text-white/70 min-w-0">
          <span className={`h-2 w-2 rounded-full ${datos.fuente === 'backend' ? 'bg-[#6aa43a] animate-pulse' : datos.fuente === 'sin_conexion' ? 'bg-rose-500' : 'bg-zinc-500'}`} />
          <span className="hidden 2xl:inline" title={etiquetaDatos}>{etiquetaDatos} · <strong className="text-white">{convocatorias.length}</strong> activas{proximaSync && datos.fuente === 'backend' ? ` · próx. sync ${new Date(proximaSync).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}` : ''}</span>
          <span className="2xl:hidden truncate" title={`${etiquetaDatos} · ${convocatorias.length} activas`}>{datos.fuente === 'backend' ? 'En vivo' : datos.fuente === 'sin_conexion' ? 'Sin conexión' : 'Cargando'}</span>
          <button onClick={handleSync} disabled={syncing} className="p-1 text-white/60 hover:text-white disabled:opacity-50" title="Actualizar ahora">
            <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
