'use client';

import React from 'react';
import { RefreshCw, Sprout } from 'lucide-react';
import { Bosque } from '@/components/Bosque';
import { Convocatoria } from '@/types/convocatoria';

export type Seccion = 'mapa' | 'convocatorias' | 'calendario' | 'empresas' | 'pipeline';

interface HeaderProps {
  convocatorias: Convocatoria[];
  seccion: Seccion;
  setSeccion: (seccion: Seccion) => void;
  onRefresh?: () => void;
}

export function Header({ seccion, setSeccion, onRefresh }: HeaderProps) {

  const secciones = [
    { id: 'mapa', label: 'Mapa' },
    { id: 'convocatorias', label: 'Convocatorias' },
    { id: 'calendario', label: 'Calendario' },
    { id: 'empresas', label: 'Empresas' },
    { id: 'pipeline', label: 'Pipeline' },
  ] as const;

  return (
    <header className="sticky top-0 z-30">
      {/* Barra de utilidad (como reforesta.es) */}
      <div className="bg-black text-white text-xs">
        <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 h-10 flex items-center justify-between">
          <span className="hidden sm:flex items-center gap-3 text-zinc-200"><span>info@reforesta.es</span><span className="text-zinc-600">|</span><span className="text-brand">NEWSLETTER</span><span className="text-zinc-600">|</span><span>HAZTE SOCIO</span></span>
          <span className="uppercase tracking-wide">Declarada de utilidad pública</span>
          <div className="hidden sm:flex items-center gap-1.5 text-zinc-300">
            {onRefresh && (
              <button onClick={onRefresh} className="ml-1 p-1 rounded text-zinc-400 hover:text-white" title="Actualizar datos">
                <RefreshCw className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Navegación principal */}
      <div className="relative bg-[#333] overflow-hidden">
        <svg aria-hidden className="absolute inset-0 h-full w-full" preserveAspectRatio="none" viewBox="0 0 1440 300">
          <Bosque semilla={13} altura={230} color="#1a1a1a" opacidad={0.55} />
        </svg>
        <div className="relative max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 h-[70px] flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 text-brand">
            <span className="font-serif tracking-[0.2em] text-sm font-bold">REFORESTA</span>
            <Sprout className="h-4 w-4" />
          </div>

          <nav className="flex items-center gap-1 text-sm sm:text-[15px] font-semibold uppercase overflow-x-auto">
            {secciones.map((v) => (
              <button
                key={v.id}
                onClick={() => setSeccion(v.id)}
                className={`px-3 sm:px-4 py-1.5 whitespace-nowrap uppercase transition-colors ${
                  seccion === v.id ? 'text-brand' : 'text-white hover:text-brand-light'
                }`}
              >
                {v.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
