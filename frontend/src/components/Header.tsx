'use client';

import React from 'react';
import { RefreshCw, Sprout } from 'lucide-react';
import { Bosque } from '@/components/Bosque';
import { Convocatoria } from '@/types/convocatoria';

export type Seccion = 'radar' | 'empresas' | 'pipeline';

interface HeaderProps {
  convocatorias: Convocatoria[];
  seccion: Seccion;
  setSeccion: (seccion: Seccion) => void;
  onRefresh?: () => void;
}

export function Header({ seccion, setSeccion, onRefresh }: HeaderProps) {

  const secciones = [
    { id: 'radar', label: 'Radar' },
    { id: 'empresas', label: 'Empresas (RSC)' },
    { id: 'pipeline', label: 'Pipeline' },
  ] as const;

  return (
    <header className="sticky top-0 z-30">
      {/* Barra de utilidad (como reforesta.es) */}
      <div className="bg-black text-white text-[11px]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-8 flex items-center justify-between">
          <span className="text-zinc-300 hidden sm:block">Radar de financiación · 1hack A Coruña</span>
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
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 text-brand">
            <span className="font-serif tracking-[0.2em] text-sm font-bold">REFORESTA</span>
            <Sprout className="h-4 w-4" />
          </div>

          <nav className="flex items-center gap-1 text-[11px] sm:text-xs font-semibold uppercase tracking-wide overflow-x-auto">
            {secciones.map((v) => (
              <button
                key={v.id}
                onClick={() => setSeccion(v.id)}
                className={`px-2.5 sm:px-3 py-1.5 whitespace-nowrap transition-colors ${
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
