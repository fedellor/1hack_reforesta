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
  setSeccion: (s: Seccion) => void;
  datos: EstadoDatos;
  onRefresh: () => void | Promise<void>;
}

const ITEMS_MENU: { id: Seccion; label: string }[] = [
  { id: 'mapa', label: 'Mapa' },
  { id: 'convocatorias', label: 'Convocatorias' },
  { id: 'empresas', label: 'Empresas RSC' },
  { id: 'pipeline', label: 'Pipeline' },
];

export function Header({ convocatorias, seccion, setSeccion, datos, onRefresh }: HeaderProps) {
  const [syncing, setSyncing] = useState(false);

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
      : datos.fuente === 'ejemplo'
        ? 'Datos de ejemplo · radar sin conexión'
        : 'Cargando datos…';

  const handleSync = async () => {
    setSyncing(true);
    try {
      await onRefresh();
    } finally {
      setTimeout(() => setSyncing(false), 600);
    }
  };

  return (
    <header className="w-full sticky top-0 z-50 shadow-md">
      {/* Top Bar idéntico a https://reforesta.es/ (#Top_bar / Action bar) */}
      <div className="bg-[#141414] text-white/90 text-[12px] py-2 px-4 sm:px-6 lg:px-8 border-b border-white/10">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
          {/* Izquierda: info@reforesta.es | NEWSLETTER | HAZTE SOCIO */}
          <div className="flex items-center flex-wrap gap-3 sm:gap-4">
            <a
              href="mailto:info@reforesta.es"
              className="hover:text-[#6aa43a] transition-colors flex items-center gap-1.5"
            >
              <span className="text-[#6aa43a]">✉</span>
              <span>info@reforesta.es</span>
            </a>
            <a
              href="https://reforesta.es/suscripcion-al-boletin-de-reforesta/"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-[#6aa43a] hover:bg-[#598c30] text-white font-semibold px-2 py-0.5 rounded-[2px] text-[11px] tracking-wider uppercase transition-colors"
            >
              NEWSLETTER
            </a>
            <a
              href="https://reforesta.es/colabora-hazte-socio-de-reforesta/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold hover:text-[#6aa43a] transition-colors tracking-wide uppercase text-[11px]"
            >
              HAZTE SOCIO
            </a>
          </div>

          {/* Centro: DECLARADA DE UTILIDAD PÚBLICA */}
          <div className="hidden lg:flex items-center">
            <a
              href="https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#c2c2c2] hover:text-white tracking-wider uppercase text-[11px] font-medium transition-colors"
            >
              DECLARADA DE UTILIDAD PÚBLICA
            </a>
          </div>

          {/* Derecha: Redes Sociales oficiales + Sincronización Radar */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5">
              <a
                href="https://www.facebook.com/asociacion.reforesta/"
                target="_blank"
                rel="noopener noreferrer"
                title="Facebook Reforesta"
                className="w-6 h-6 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[11px] font-bold transition-colors"
              >
                f
              </a>
              <a
                href="https://x.com/Reforesta_ONG"
                target="_blank"
                rel="noopener noreferrer"
                title="X (Twitter) Reforesta"
                className="w-6 h-6 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[11px] font-bold transition-colors"
              >
                𝕏
              </a>
              <a
                href="https://www.instagram.com/reforesta_ong/?hl=es"
                target="_blank"
                rel="noopener noreferrer"
                title="Instagram Reforesta"
                className="w-6 h-6 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[10px] font-bold transition-colors"
              >
                IG
              </a>
              <a
                href="https://www.youtube.com/c/Reforesta_ong"
                target="_blank"
                rel="noopener noreferrer"
                title="YouTube Reforesta"
                className="w-6 h-6 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[10px] font-bold transition-colors"
              >
                ▶
              </a>
              <a
                href="https://es.linkedin.com/company/asociacion-reforesta"
                target="_blank"
                rel="noopener noreferrer"
                title="LinkedIn Reforesta"
                className="w-6 h-6 rounded-full bg-white/10 hover:bg-[#6aa43a] flex items-center justify-center text-white text-[11px] font-bold transition-colors"
              >
                in
              </a>
            </div>

            <span className="text-white/20 hidden sm:inline">|</span>

            <span className="hidden md:inline-flex items-center gap-1.5 text-white/70 text-[11px]">
              <span className={`h-2 w-2 rounded-full ${datos.fuente === 'backend' ? 'bg-[#6aa43a] animate-pulse' : datos.fuente === 'ejemplo' ? 'bg-amber-400' : 'bg-zinc-500'}`} />
              {etiquetaDatos} · <strong className="text-white">{convocatorias.length}</strong> activas
            </span>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-1.5 text-[#7cc142] hover:text-white transition-colors font-semibold text-[11px] uppercase tracking-wider cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'Sincronizando...' : 'Sincronizar Fuentes'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar idéntica a https://reforesta.es/ (fondo oscuro translúcido + logo verde oficial + menú uppercase) */}
      <div className="bg-[#1a1a1a]/92 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[72px] flex items-center justify-between gap-4">
          {/* Logo Oficial Reforesta */}
          <div className="flex items-center gap-4 shrink-0">
            <a
              href="https://reforesta.es/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group"
              title="Ir a reforesta.es"
            >
              <img
                src="/reforesta/logo-reforesta-verde.png"
                alt="Reforesta"
                className="h-[34px] sm:h-[38px] w-auto object-contain transition-transform group-hover:scale-[1.02]"
              />
            </a>
            <span className="hidden xl:inline-block text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6aa43a] border-l border-white/20 pl-3 py-0.5">
              Radar de Financiación Forestal
            </span>
          </div>

          {/* Navegación principal estilo Reforesta (Open Sans 14px uppercase blanca con acento verde #6aa43a) */}
          <nav className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto">
            {ITEMS_MENU.map((item) => {
              const activo = seccion === item.id || (item.id === 'convocatorias' && seccion === 'calendario');
              return (
                <button
                  key={item.id}
                  onClick={() => setSeccion(item.id)}
                  className={`relative px-2.5 sm:px-3.5 py-2 text-[12px] sm:text-[13px] font-semibold uppercase tracking-[0.06em] transition-colors cursor-pointer whitespace-nowrap ${
                    activo
                      ? 'text-[#7cc142]'
                      : 'text-white/90 hover:text-[#7cc142]'
                  }`}
                >
                  {item.label}
                  {activo && (
                    <span className="absolute left-2.5 right-2.5 -bottom-[17px] h-[3px] bg-[#6aa43a]" />
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
