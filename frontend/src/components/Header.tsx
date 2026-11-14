'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

export interface EstadoDatos {
  fuente: 'cargando' | 'backend' | 'sin_conexion';
  actualizado: Date | null;
}

export type Seccion = 'mapa' | 'plan' | 'prevision' | 'historico' | 'empresas';

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
  /** Enlace oficial a los estatutos de Reforesta */
  estatutosPdfUrl?: string;
}

const ITEMS_MENU: { id: Seccion; label: string }[] = [
  { id: 'mapa', label: 'Mapa' },
  { id: 'plan', label: 'Plan de ataque' },
  { id: 'prevision', label: 'Previsión' },
  { id: 'historico', label: 'Histórico' },
  { id: 'empresas', label: 'Empresas' },
];

export function Header({
  convocatorias,
  seccion,
  setSeccion,
  datos,
  onRefresh,
  nuevas = 0,
  proximaSync = null,
  estatutosPdfUrl = 'https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf',
}: HeaderProps) {
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
  const minutos =
    datos.actualizado && ahora
      ? Math.max(0, Math.round((ahora - datos.actualizado.getTime()) / 60000))
      : null;
  const minLabel = minutos === null || minutos < 1 ? 'ahora' : `hace ${minutos}m`;
  const syncTitle =
    proximaSync && datos.fuente === 'backend'
      ? `Datos en vivo (${minLabel}) · Sincronización diaria automática 07:00h (próx. ${new Date(proximaSync).toLocaleTimeString('es-ES', {
          hour: '2-digit',
          minute: '2-digit',
        })})`
      : 'Sincronización diaria automática 07:00h (BDNS · BOE · PLACSP · TED · 19 CCAA · UE · RSC)';

  return (
    <header className="w-full sticky top-0 z-50 bg-[#141414]/95 backdrop-blur-md border-b border-white/10 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-[54px] py-1.5 flex items-center justify-between gap-3">
        {/* Identidad corporativa mínima */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/reforesta/logo-reforesta-verde.png"
            alt="Reforesta"
            className="h-[22px] sm:h-[24px] w-auto object-contain"
          />
          <span className="hidden lg:inline-block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#7cc142] border-l border-white/15 pl-2.5">
            Radar Forestal
          </span>
        </div>

        {/* Navegación limpia sin scrollbars internos */}
        <nav className="flex items-center flex-wrap justify-center gap-0.5 sm:gap-1">
          {ITEMS_MENU.map((item) => {
            const activo = seccion === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setSeccion(item.id)}
                className={`px-2.5 sm:px-3 py-1.5 border-b-2 text-[11px] sm:text-[12px] font-semibold uppercase tracking-[0.06em] transition-colors cursor-pointer whitespace-nowrap ${
                  activo
                    ? 'border-[#6aa43a] text-[#7cc142]'
                    : 'border-transparent text-white/85 hover:text-[#7cc142]'
                }`}
              >
                {item.label}
                {item.id === 'plan' && nuevas > 0 && (
                  <span
                    className="ml-1.5 rounded-full bg-[#6aa43a] px-1.5 py-0.5 text-[10px] font-bold text-white align-middle"
                    title="Nuevas desde tu última visita"
                  >
                    {nuevas}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Estado en vivo y acciones rápidas */}
        <div className="flex items-center gap-3 shrink-0">
          <div
            title={syncTitle}
            className="hidden sm:flex items-center gap-1.5 text-[10px] text-zinc-300"
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                datos.fuente === 'backend'
                  ? 'bg-[#7cc142] animate-pulse'
                  : datos.fuente === 'sin_conexion'
                    ? 'bg-rose-500'
                    : 'bg-zinc-500'
              }`}
            />
            <span className="text-white/90 font-medium">{convocatorias.length} activas</span>
          </div>

          <a
            href={estatutosPdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:inline text-zinc-300 hover:text-[#7cc142] tracking-wider uppercase text-[10px] font-medium transition-colors"
          >
            Estatutos
          </a>

          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            title="Actualizar convocatorias y licitaciones ahora"
            className="flex items-center gap-1 rounded-full bg-white/10 hover:bg-[#6aa43a] px-2.5 py-1 text-white transition-colors font-semibold text-[10px] uppercase tracking-wider cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${syncing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{syncing ? 'Sincronizando' : 'Actualizar'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
