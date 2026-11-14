'use client';

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { EmbudoReal } from '@/services/api';
import { formatoEuros } from '@/lib/territorio';
import { plazoSinFijar } from '@/lib/plazo';

const HORAS_LECTURA_POR_CONVOCATORIA = 3;

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
}

const REFORESTA_SLIDES: SlideItem[] = [
  {
    id: 'slide-bosques',
    image: '/reforesta/reforesta-slider-01.jpg',
    linea1: 'Radar de subvenciones y',
    linea2: 'licitaciones forestales',
    subtexto: 'Filtra al instante ayudas públicas, contratos y mecenazgo compatibles con Reforesta.',
  },
  {
    id: 'slide-reforestacion',
    image: '/reforesta/reforesta-slider-03.jpg',
    linea1: 'Seguimiento automático',
    linea2: 'desde 2016 a 2027',
    subtexto: 'BDNS, BOE, TED/PLACSP, 19 CCAA, UE y fundaciones privadas sincronizados cada día.',
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
    <div className="relative bg-[#1b2c1f] text-white overflow-hidden select-none border-b-4 border-brand">
      {/* Carrusel compacto con las 2 imágenes reales de Reforesta */}
      <div className="relative h-[120px] sm:h-[136px] w-full overflow-hidden">
        <div
          className="flex h-full w-full transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${activeIndex * 100}%)` }}
        >
          {REFORESTA_SLIDES.map((slide) => (
            <div key={slide.id} className="relative min-w-full h-full overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={slide.image}
                alt={`${slide.linea1} ${slide.linea2}`}
                className="w-full h-full object-cover object-center scale-[1.01]"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black/75 via-black/45 to-black/65" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/25" />
            </div>
          ))}
        </div>

        {/* Contenido superpuesto */}
        <div className="absolute inset-0 z-10 flex items-center">
          <div className="max-w-7xl mx-auto px-12 sm:px-16 lg:px-20 w-full flex flex-col lg:flex-row lg:items-center justify-between gap-5">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 bg-[#6aa43a] text-white text-[10px] font-bold uppercase tracking-[0.14em] px-2.5 py-0.5 mb-1.5 shadow-sm">
                <span>Reforesta · Uso Interno</span>
              </div>
              <h2 className="text-xl sm:text-2xl md:text-[28px] font-light leading-[1.1] tracking-tight text-white drop-shadow-md">
                {REFORESTA_SLIDES[activeIndex].linea1}{' '}
                <span className="font-bold text-[#7cc142]">
                  {REFORESTA_SLIDES[activeIndex].linea2}
                </span>
              </h2>
              <p className="mt-1 text-xs text-white/95 font-light drop-shadow">
                {REFORESTA_SLIDES[activeIndex].subtexto}
              </p>
            </div>

            {/* Tarjeta derecha minimalista con vista actual */}
            <div className="hidden md:block bg-black/60 backdrop-blur-md border-l-4 border-[#6aa43a] px-3.5 py-2.5 max-w-xs rounded-r-sm shadow-lg">
              <div className="text-[9px] uppercase tracking-[0.14em] text-[#7cc142] font-semibold">
                {migas}
              </div>
              <h1 className="text-base font-serif font-bold text-white leading-snug">
                {titulo}
              </h1>
              <p className="text-[11px] text-white/80 mt-0.5 line-clamp-2 leading-snug">
                {subtitulo ||
                  'Solo oportunidades aptas para Reforesta o motivo exacto de exclusión.'}
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={prevSlide}
          aria-label="Imagen anterior"
          className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-black/50 hover:bg-[#6aa43a] text-white flex items-center justify-center transition-colors cursor-pointer border border-white/20"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={nextSlide}
          aria-label="Imagen siguiente"
          className="absolute right-3 sm:right-4 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-black/50 hover:bg-[#6aa43a] text-white flex items-center justify-center transition-colors cursor-pointer border border-white/20"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        <div className="absolute bottom-2.5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
          {REFORESTA_SLIDES.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveIndex(idx)}
              aria-label={`Ir a imagen ${idx + 1}`}
              className={`h-2 transition-all cursor-pointer rounded-full ${idx === activeIndex ? 'w-6 bg-[#6aa43a]' : 'w-2 bg-white/50 hover:bg-white/90'
                }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function Embudo({
  convocatorias,
  embudo,
}: {
  convocatorias: Convocatoria[];
  embudo: EmbudoReal | null;
}) {
  const real = embudo !== null && embudo.detectadas > 0;
  const detectadas = real ? Math.max(embudo.detectadas, convocatorias.length) : convocatorias.length;
  const aptas = convocatorias.filter((c) => c.elegible);
  const en30 = aptas.filter(
    (c) => c.estado !== 'PROXIMA' && !plazoSinFijar(c) && c.diasRestantes <= 30
  );
  const altoEncaje = aptas.filter((c) => c.matchingGlobal >= 80);
  const fondos = altoEncaje.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const descartadas = Math.max(0, detectadas - aptas.length);
  const horasAhorradas = descartadas * HORAS_LECTURA_POR_CONVOCATORIA;

  const pasos = [
    {
      n: detectadas,
      etiqueta: 'Escaneadas en fuentes',
      nota: real ? 'BDNS, BOE, TED/PLACSP, UE, CCAA y RSC' : 'convocatorias verificadas en España',
    },
    {
      n: aptas.length,
      etiqueta: 'Aptas para Reforesta',
      nota: 'cumplen NIF G80428204 y fines ESAL',
    },
    {
      n: en30.length,
      etiqueta: 'Cierran en ≤ 30 días',
      nota: 'prioridad de presentación',
    },
    {
      n: altoEncaje.length,
      etiqueta: 'Encaje ≥ 80%',
      nota: fondos > 0 ? `${formatoEuros(fondos)} máx. acumulado` : 'sin importe fijo en bases',
    },
  ];

  return (
    <section className="bg-white border-b border-zinc-200">
      <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <ol className="grid grid-cols-2 lg:grid-cols-4 gap-y-5">
          {pasos.map((p, i) => (
            <li
              key={p.etiqueta}
              className={`px-5 ${i > 0 ? 'lg:border-l border-zinc-200' : ''} ${i % 2 === 1 ? 'border-l border-zinc-200 lg:border-l' : ''
                }`}
            >
              <span
                className={`font-serif text-3xl sm:text-4xl font-bold tabular-nums ${i === pasos.length - 1 ? 'text-[#6aa43a]' : 'text-zinc-900'
                  }`}
              >
                {p.n}
              </span>
              <span className="block mt-1 text-xs font-bold uppercase tracking-wide text-zinc-900">
                {p.etiqueta}
              </span>
              <span className="block text-xs text-zinc-500 mt-0.5">{p.nota}</span>
            </li>
          ))}
        </ol>
        <div className="mt-4 px-5 flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-500 border-t border-zinc-100 pt-3">
          <span>
            ≈ <strong className="text-zinc-700">{horasAhorradas} h</strong> de lectura de bases evitadas (
            {HORAS_LECTURA_POR_CONVOCATORIA} h por convocatoria excluida o filtrada).
          </span>
          <span className="text-[#2d5a27] font-medium">
            Sincronización automática diaria programada a las 07:00h (Europe/Madrid)
          </span>
        </div>
      </div>
    </section>
  );
}
