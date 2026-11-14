'use client';

import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

export interface EstadoDatos {
  fuente: 'cargando' | 'backend' | 'ejemplo';
  actualizado: Date | null;
}

export type Seccion = 'mapa' | 'convocatorias' | 'calendario' | 'empresas' | 'pipeline';

interface HeaderProps {
  convocatorias: Convocatoria[];
  seccion: Seccion;
  setSeccion: (seccion: Seccion) => void;
  datos: EstadoDatos;
  onRefresh?: () => Promise<void> | void;
}

const ITEMS_MENU: { id: Seccion; label: string }[] = [
  { id: 'mapa', label: 'Mapa' },
  { id: 'convocatorias', label: 'Convocatorias' },
  { id: 'calendario', label: 'Calendario' },
  { id: 'empresas', label: 'Empresas RSC' },
  { id: 'pipeline', label: 'Pipeline' },
];

export function Header({ convocatorias, seccion, setSeccion, datos, onRefresh }: HeaderProps) {
  const [syncing, setSyncing] = useState(false);
  const [ahora, setAhora] = useState(0);

  useEffect(() => {
    setAhora(Date.now());
    const t = setInterval(() => setAhora(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);

  const minutos =
    datos.actualizado && ahora ? Math.max(0, Math.round((ahora - datos.actualizado.getTime()) / 60000)) : null;
  const etiquetaDatos =
    datos.fuente === 'backend'
      ? `En vivo · ${minutos === null || minutos < 1 ? 'ahora' : `hace ${minutos}m`}`
      : datos.fuente === 'ejemplo'
        ? 'Sin conexión al radar'
        : 'Cargando…';

  const handleSync = async () => {
    if (!onRefresh) return;
    setSyncing(true);
    try {
      await onRefresh();
    } finally {
      setTimeout(() => setSyncing(false), 500);
    }
  };

  return (
    <header className="w-full sticky top-0 z-40 shadow-sm">
      {/* Barra superior compacta inspirada en https://reforesta.es/ */}
      <div className="bg-[#141414] text-white/90 text-[11px] py-1 px-4 sm:px-6 lg:px-8 border-b border-white/10">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          {/* Izquierda: Contacto + Newsletter + Hazte socio */}
          <div className="flex items-center flex-wrap gap-2.5 sm:gap-3">
            <a
              href="mailto:info@reforesta.es"
              className="hover:text-[#7cc142] transition-colors flex items-center gap-1"
            >
              <span className="text-[#6aa43a]">✉</span>
              <span>info@reforesta.es</span>
            </a>
            <a
              href="https://reforesta.es/suscripcion-al-boletin-de-reforesta/"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#6aa43a] hover:bg-[#598c30] text-white font-semibold px-1.5 py-0.5 rounded-[2px] text-[10px] tracking-wider uppercase transition-colors"
            >
              NEWSLETTER
            </a>
            <a
              href="https://reforesta.es/colabora-hazte-socio-de-reforesta/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold hover:text-[#7cc142] transition-colors tracking-wide uppercase text-[10px]"
            >
              HAZTE SOCIO
            </a>
          </div>

          {/* Centro: Declarada de Utilidad Pública (enlace directo al documento oficial) */}
          <div className="hidden lg:flex items-center gap-2">
            <a
              href="https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#c2c2c2] hover:text-white tracking-wider uppercase text-[10px] font-medium transition-colors"
            >
              DECLARADA DE UTILIDAD PÚBLICA
            </a>
            <span className="text-white/25">·</span>
            <a
              href="https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#c2c2c2] hover:text-[#7cc142] tracking-wider uppercase text-[10px] font-medium transition-colors"
            >
              ESTATUTOS PDF
            </a>
          </div>

          {/* Derecha: Estado en vivo + Sync 07:00 + Redes */}
          <div className="flex items-center gap-2.5">
            <div className="hidden sm:flex items-center gap-1">
              <a
                href="https://www.facebook.com/asociacion.reforesta/"
                target="_blank"
                rel="noopener noreferrer"
                title="Facebook Reforesta"
                className="w-4 h-4 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[9px] font-bold transition-colors"
              >
                f
              </a>
              <a
                href="https://x.com/Reforesta_ONG"
                target="_blank"
                rel="noopener noreferrer"
                title="X Reforesta"
                className="w-4 h-4 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[9px] font-bold transition-colors"
              >
                𝕏
              </a>
              <a
                href="https://www.instagram.com/reforesta_ong/?hl=es"
                target="_blank"
                rel="noopener noreferrer"
                title="Instagram Reforesta"
                className="w-4 h-4 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[8px] font-bold transition-colors"
              >
                IG
              </a>
              <a
                href="https://es.linkedin.com/company/asociacion-reforesta"
                target="_blank"
                rel="noopener noreferrer"
                title="LinkedIn Reforesta"
                className="w-4 h-4 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[9px] font-bold transition-colors"
              >
                in
              </a>
            </div>

            <span className="text-white/20 hidden sm:inline">|</span>

            <div className="flex items-center gap-1.5 text-[10px] text-zinc-300">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  datos.fuente === 'backend'
                    ? 'bg-[#7cc142] animate-pulse'
                    : datos.fuente === 'ejemplo'
                      ? 'bg-amber-400'
                      : 'bg-zinc-500'
                }`}
              />
              <span>{etiquetaDatos}</span>
              <span className="hidden xl:inline text-white/40">· Sync 07:00h</span>
              <span className="hidden md:inline text-white/70">
                ({convocatorias.length})
              </span>
            </div>

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
          {/* Logo Oficial Reforesta (tamaño compacto) */}
          <div className="flex items-center gap-3 shrink-0">
            <a
              href="https://reforesta.es/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 group"
              title="Ir a reforesta.es"
            >
              <img
                src="/reforesta/logo-reforesta-verde.png"
                alt="Reforesta"
                className="h-[24px] sm:h-[26px] w-auto object-contain transition-transform group-hover:scale-[1.02]"
              />
            </a>
            <span className="hidden xl:inline-block text-[10px] font-semibold uppercase tracking-[0.16em] text-[#7cc142] border-l border-white/20 pl-2.5 py-0.5">
              Radar de Financiación Forestal
            </span>
          </div>

          {/* Navegación principal */}
          <nav className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto">
            <a
              href="https://reforesta.es/"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:inline-flex items-center px-2.5 py-1.5 text-[12px] font-semibold uppercase tracking-[0.06em] text-white/75 hover:text-[#7cc142] transition-colors"
            >
              Web Reforesta
            </a>
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
