'use client';

import React, { useEffect, useState } from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { EmbudoReal } from '@/services/api';
import { plazoSinFijar } from '@/lib/plazo';


interface HeroProps {
  titulo: string;
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

export function Hero({ titulo }: HeroProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % REFORESTA_SLIDES.length);
    }, 5500);
    return () => clearInterval(timer);
  }, []);

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
                alt=""
                className="w-full h-full object-cover object-center scale-[1.01]"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/25 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/25" />
            </div>
          ))}
        </div>

        {/* Solo el título de la sección */}
        <div className="absolute inset-0 z-10 flex items-center">
          <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <h1 className="font-sans text-2xl sm:text-[28px] font-light tracking-tight text-white drop-shadow-md">{titulo}</h1>
          </div>
        </div>

        <div className="absolute bottom-3 right-6 z-20 flex items-center gap-1.5">
          {REFORESTA_SLIDES.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveIndex(idx)}
              aria-label={`Ir a imagen ${idx + 1}`}
              className={`h-1.5 transition-all cursor-pointer rounded-full ${idx === activeIndex ? 'w-5 bg-[#6aa43a]' : 'w-1.5 bg-white/50 hover:bg-white/90'
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

  const pasos = [
    {
      n: detectadas,
      etiqueta: 'Escaneadas en fuentes',
    },
    {
      n: aptas.length,
      etiqueta: 'Aptas para Reforesta',
    },
    {
      n: en30.length,
      etiqueta: 'Cierran en ≤ 30 días',
    },
    {
      n: altoEncaje.length,
      etiqueta: 'Encaje ≥ 80%',
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
            </li>
          ))}
        </ol>
        <div className="mt-4 px-5 flex flex-wrap items-center justify-end gap-2 text-[11px] text-zinc-500 border-t border-zinc-100 pt-3">
          <span className="text-[#2d5a27] font-medium">
            Sincronización automática diaria programada a las 07:00h (Europe/Madrid)
          </span>
        </div>
      </div>
    </section>
  );
}
