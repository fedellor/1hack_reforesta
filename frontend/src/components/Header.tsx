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
  const etiquetaDatos =
    datos.fuente === 'backend'
      ? `En vivo · ${minutos === null || minutos < 1 ? 'ahora' : `hace ${minutos} min`}`
      : datos.fuente === 'sin_conexion'
        ? 'Sin conexión con el radar'
        : 'Cargando…';

  return (
    <header className="w-full sticky top-0 z-50 shadow-sm">
      {/* Barra superior interna con identidad Reforesta */}
      <div className="bg-[#141414] text-white/90 text-[11px] py-1 px-4 sm:px-6 lg:px-8 border-b border-white/10">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          <div className="flex items-center gap-2 text-[10px] tracking-wider uppercase text-zinc-300">
            <span className="h-1.5 w-1.5 rounded-full bg-[#6aa43a]" />
            <span className="font-semibold text-white">Herramienta Interna · Reforesta</span>
            <span className="hidden md:inline text-white/30">|</span>
            <span className="hidden md:inline text-zinc-400">
              Sync automática 07:00h (BDNS · BOE · 19 CCAA · PLACSP · UE)
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[10px] text-zinc-300">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  datos.fuente === 'backend'
                    ? 'bg-[#7cc142] animate-pulse'
                    : datos.fuente === 'sin_conexion'
                      ? 'bg-rose-500'
                      : 'bg-zinc-500'
                }`}
              />
              <span>{etiquetaDatos}</span>
              <span className="hidden sm:inline text-white/75">
                · <strong className="text-white">{convocatorias.length}</strong> abiertas
                {proximaSync && datos.fuente === 'backend'
                  ? ` · próx. sync ${new Date(proximaSync).toLocaleTimeString('es-ES', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}`
                  : ''}
              </span>
            </div>

            <a
              href={estatutosPdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline text-[#c2c2c2] hover:text-[#7cc142] tracking-wider uppercase text-[10px] font-medium transition-colors"
            >
              Estatutos PDF
            </a>

            <button
              onClick={handleSync}
              disabled={syncing}
              title="Actualizar convocatorias desde el servidor"
              className="flex items-center gap-1 text-[#7cc142] hover:text-white transition-colors font-semibold text-[10px] uppercase tracking-wider cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${syncing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{syncing ? 'Actualizando' : 'Actualizar'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navegación principal compacta */}
      <div className="bg-[#1a1a1a]/95 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[50px] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/reforesta/logo-reforesta-verde.png"
              alt="Reforesta"
              className="h-[24px] sm:h-[26px] w-auto object-contain"
            />
            <span className="hidden xl:inline-block text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7cc142] border-l border-white/20 pl-2.5 py-0.5">
              Radar Interno de Subvenciones
            </span>
          </div>

          <nav className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto min-w-0">
            {ITEMS_MENU.map((item) => {
              const activo = seccion === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setSeccion(item.id)}
                  className={`relative px-2.5 sm:px-3 py-1.5 text-[12px] font-semibold uppercase tracking-[0.06em] transition-colors cursor-pointer whitespace-nowrap ${
                    activo ? 'text-[#7cc142]' : 'text-white/90 hover:text-[#7cc142]'
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
                  {activo && (
                    <span className="absolute left-2.5 right-2.5 -bottom-[10px] h-[2.5px] bg-[#6aa43a]" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
