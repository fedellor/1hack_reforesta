'use client';

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

interface HeroProps {
  titulo: string;
  migas: string;
  subtitulo?: string;
}

interface SlideItem {
  id: string;
  image: string;
  linea1: string;
  linea2: string;
  subtexto: string;
  ctaLabel: string;
  ctaUrl: string;
}

const REFORESTA_SLIDES: SlideItem[] = [
  {
    id: 'slide-bosques',
    image: '/reforesta/reforesta-slider-01.jpg',
    linea1: 'Buscamos',
    linea2: 'tu ayuda',
    subtexto: 'Para recuperar los bosques · Radar de Financiación Forestal en España',
    ctaLabel: 'LEER MÁS',
    ctaUrl: 'https://reforesta.es/colabora-hazte-socio-de-reforesta/',
  },
  {
    id: 'slide-regala-arbol',
    image: '/reforesta/reforesta-slider-03.jpg',
    linea1: 'Regala un',
    linea2: 'árbol',
    subtexto: 'Para cambiar el mundo · Reforestación con especies autóctonas en territorio español',
    ctaLabel: 'LEER MÁS',
    ctaUrl: 'https://reforesta.es/regala-un-arbol-edicion-limitada/',
  },
  {
    id: 'slide-desertificacion',
    image: '/reforesta/cabecera-desertificacion.jpg',
    linea1: 'Desertificación',
    linea2: 'en España',
    subtexto: 'En qué punto estamos · Captación de fondos públicos y privados para restaurar ecosistemas',
    ctaLabel: 'LEER MÁS',
    ctaUrl: 'https://reforesta.es/desertificacion/',
  },
];

export function Hero({ titulo, migas, subtitulo }: HeroProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % REFORESTA_SLIDES.length);
    }, 5500);
    return () => clearInterval(timer);
  }, []);

  const prevSlide = () => {
    setActiveIndex((prev) => (prev - 1 + REFORESTA_SLIDES.length) % REFORESTA_SLIDES.length);
  };

  const nextSlide = () => {
    setActiveIndex((prev) => (prev + 1) % REFORESTA_SLIDES.length);
  };

  return (
    <div className="relative bg-[#1b2c1f] text-white overflow-hidden select-none">
      {/* Carrusel de imágenes reales de https://reforesta.es/ con deslizamiento suave */}
      <div className="relative h-[320px] sm:h-[380px] md:h-[430px] w-full overflow-hidden">
        <div
          className="flex h-full w-full transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${activeIndex * 100}%)` }}
        >
          {REFORESTA_SLIDES.map((slide) => (
            <div key={slide.id} className="relative min-w-full h-full overflow-hidden">
              <img
                src={slide.image}
                alt={`${slide.linea1} ${slide.linea2}`}
                className="w-full h-full object-cover object-center scale-[1.02] transition-transform duration-1000"
              />
              {/* Velo oscuro degradado estilo Slider Revolution de reforesta.es */}
              <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/45 to-black/60" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30" />
            </div>
          ))}
        </div>

        {/* Contenido superpuesto: Titular corporativo de Reforesta + Sección activa del Radar */}
        <div className="absolute inset-0 z-10 flex items-center">
          <div className="max-w-7xl mx-auto px-12 sm:px-16 lg:px-20 w-full flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            {/* Bloque izquierdo: Tipografía idéntica al Slider de reforesta.es */}
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-2 bg-[#6aa43a] text-white text-[11px] font-bold uppercase tracking-[0.15em] px-3 py-1 mb-3 shadow-sm">
                <span>Asociación Reforesta · Utilidad Pública</span>
              </div>
              <h2 className="text-4xl sm:text-5xl md:text-6xl font-light leading-[1.05] tracking-tight text-white drop-shadow-md">
                {REFORESTA_SLIDES[activeIndex].linea1}{' '}
                <span className="font-bold text-[#7cc142]">
                  {REFORESTA_SLIDES[activeIndex].linea2}
                </span>
              </h2>
              <p className="mt-3 text-base sm:text-lg text-white/95 font-light drop-shadow">
                {REFORESTA_SLIDES[activeIndex].subtexto}
              </p>
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <a
                  href={REFORESTA_SLIDES[activeIndex].ctaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center bg-[#262626]/90 hover:bg-[#6aa43a] text-white text-[12px] font-semibold uppercase tracking-[0.12em] px-6 py-2.5 border border-white/25 hover:border-[#6aa43a] transition-colors"
                >
                  {REFORESTA_SLIDES[activeIndex].ctaLabel}
                </a>
              </div>
            </div>

            {/* Bloque derecho: Sección actual de Reforesta Financiación */}
            <div className="bg-black/65 backdrop-blur-md border-l-4 border-[#6aa43a] p-4 sm:p-5 max-w-md rounded-r-sm shadow-lg">
              <div className="text-[11px] uppercase tracking-[0.16em] text-[#7cc142] font-semibold mb-1">
                Reforesta &nbsp;/&nbsp; <span className="text-white">{migas}</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-serif font-bold text-white leading-snug">
                {titulo}
              </h1>
              <p className="text-xs sm:text-sm text-white/85 mt-1.5 leading-relaxed">
                {subtitulo ||
                  'Convocatorias 100% reales de reforestación, silvicultura y prevención de incendios en territorio español.'}
              </p>
            </div>
          </div>
        </div>

        {/* Flechas laterales estilo Slider Revolution (tp-leftarrow / tp-rightarrow) */}
        <button
          onClick={prevSlide}
          aria-label="Imagen anterior"
          className="absolute left-3 sm:left-5 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-black/50 hover:bg-[#6aa43a] text-white flex items-center justify-center transition-colors cursor-pointer border border-white/20"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <button
          onClick={nextSlide}
          aria-label="Imagen siguiente"
          className="absolute right-3 sm:right-5 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-black/50 hover:bg-[#6aa43a] text-white flex items-center justify-center transition-colors cursor-pointer border border-white/20"
        >
          <ChevronRight className="w-5 h-5" />
        </button>

        {/* Indicadores inferiores de diapositiva */}
        <div className="absolute bottom-3.5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
          {REFORESTA_SLIDES.map((s, idx) => (
            <button
              key={s.id}
              onClick={() => setActiveIndex(idx)}
              aria-label={`Ir a imagen ${idx + 1}`}
              className={`h-2.5 transition-all cursor-pointer rounded-full ${
                idx === activeIndex
                  ? 'w-8 bg-[#6aa43a]'
                  : 'w-2.5 bg-white/50 hover:bg-white/90'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface EmbudoProps {
  convocatorias: Convocatoria[];
}

export function Embudo({ convocatorias }: EmbudoProps) {
  const total = convocatorias.length;
  const elegibles = convocatorias.filter((c) => c.elegible).length;
  const altaPrioridad = convocatorias.filter((c) => c.elegible && c.matchingGlobal >= 75).length;

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="flex items-center gap-4 p-3 rounded border border-gray-200 bg-[#f7f5ef]">
            <div className="text-3xl font-serif font-bold text-[#2b2b2b] tabular-nums">
              {total}
            </div>
            <div className="text-xs text-gray-600 leading-snug">
              <div className="font-semibold text-gray-800 uppercase tracking-wider">
                1. Convocatorias Reales Activas
              </div>
              Reforestación, silvicultura y prevención de incendios en España
            </div>
          </div>
          <div className="flex items-center gap-4 p-3 rounded border border-[#6aa43a]/40 bg-[#eef5e6]">
            <div className="text-3xl font-serif font-bold text-[#2d5a27] tabular-nums">
              {elegibles}
            </div>
            <div className="text-xs text-gray-700 leading-snug">
              <div className="font-semibold text-[#2d5a27] uppercase tracking-wider">
                2. Elegibles para Reforesta
              </div>
              Abiertas a Asociaciones / ONG declaradas de Utilidad Pública
            </div>
          </div>
          <div className="flex items-center gap-4 p-3 rounded border border-[#2d5a27] bg-[#2d5a27] text-white">
            <div className="text-3xl font-serif font-bold text-[#a4d65e] tabular-nums">
              {altaPrioridad}
            </div>
            <div className="text-xs text-white/90 leading-snug">
              <div className="font-semibold text-white uppercase tracking-wider">
                3. Prioritarias (≥ 75% afinidad)
              </div>
              Encaje directo en restauración forestal y custodia del territorio
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
