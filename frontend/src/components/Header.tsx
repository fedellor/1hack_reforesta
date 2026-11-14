'use client';

import React from 'react';

export interface EstadoDatos {
  fuente: 'cargando' | 'backend' | 'sin_conexion';
  actualizado: Date | null;
}

export type Seccion = 'mapa' | 'plan' | 'prevision' | 'historico' | 'empresas';

interface HeaderProps {
  seccion: Seccion;
  setSeccion: (s: Seccion) => void;
}

const ITEMS_MENU: { id: Seccion; label: string }[] = [
  { id: 'mapa', label: 'Mapa' },
  { id: 'plan', label: 'Plan de ataque' },
  { id: 'empresas', label: 'Empresas' },
  { id: 'prevision', label: 'Previsión' },
  { id: 'historico', label: 'Histórico' },
];

export function Header({ seccion, setSeccion }: HeaderProps) {
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
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
