'use client';

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { EmbudoReal } from '@/services/api';
import { formatoEuros } from '@/lib/territorio';

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
  ctaLabel: string;
  ctaUrl: string;
}

const REFORESTA_SLIDES: SlideItem[] = [
  {
    id: 'slide-bosques',
    image: '/reforesta/reforesta-slider-01.jpg',
    linea1: 'Buscamos',
    linea2: 'tu ayuda',
    subtexto: 'Para recuperar los bosques · Radar oficial de financiación forestal en España',
    ctaLabel: 'CONOCER REFORESTA',
    ctaUrl: 'https://reforesta.es/colabora-hazte-socio-de-reforesta/',
  },
  {
    id: 'slide-regala-arbol',
    image: '/reforesta/reforesta-slider-03.jpg',
    linea1: 'Regala un',
    linea2: 'árbol',
    subtexto: 'Reforestación con especies autóctonas · Asociación declarada de Utilidad Pública',
    ctaLabel: 'NUESTROS PROYECTOS',
    ctaUrl: 'https://reforesta.es/nuestros-proyectos/',
  },
  {
    id: 'slide-desertificacion',
    image: '/reforesta/cabecera-desertificacion.jpg',
    linea1: 'Desertificación',
    linea2: 'en España',
    subtexto: 'Lucha contra la deforestación y erosión · Fines Estatutarios Art. 2 (NIF G80428204)',
    ctaLabel: 'VER ESTATUTOS PDF',
    ctaUrl: 'https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf',
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
      {/* Carrusel compacto con imágenes reales de https://reforesta.es/ */}
      <div className="relative h-[220px] sm:h-[250px] md:h-[275px] w-full overflow-hidden">
        <div
          className="flex h-full w-full transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${activeIndex * 100}%)` }}
        >
          {REFORESTA_SLIDES.map((slide) => (
            <div key={slide.id} className="relative min-w-full h-full overflow-hidden">
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
            <div className="max-w-xl">
              <div className="inline-flex items-center gap-2 bg-[#6aa43a] text-white text-[10px] font-bold uppercase tracking-[0.14em] px-2.5 py-0.5 mb-2 shadow-sm">
                <span>Asociación Reforesta · Desde 1991 · Utilidad Pública</span>
              </div>
              <h2 className="text-3xl sm:text-4xl md:text-[42px] font-light leading-[1.05] tracking-tight text-white drop-shadow-md">
                {REFORESTA_SLIDES[activeIndex].linea1}{' '}
                <span className="font-bold text-[#7cc142]">
                  {REFORESTA_SLIDES[activeIndex].linea2}
                </span>
              </h2>
              <p className="mt-2 text-sm sm:text-base text-white/95 font-light drop-shadow">
                {REFORESTA_SLIDES[activeIndex].subtexto}
              </p>
              <div className="mt-3.5 flex flex-wrap items-center gap-2.5">
                <a
                  href={REFORESTA_SLIDES[activeIndex].ctaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center bg-[#262626]/90 hover:bg-[#6aa43a] text-white text-[11px] font-semibold uppercase tracking-[0.12em] px-4 py-1.5 border border-white/25 hover:border-[#6aa43a] transition-colors"
                >
                  {REFORESTA_SLIDES[activeIndex].ctaLabel}
                </a>
                <a
                  href="https://reforesta.es/wp-content/uploads/2026/05/Memoria-Reforesta-2024.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center bg-black/40 hover:bg-black/70 text-white/90 text-[11px] font-medium uppercase tracking-[0.1em] px-3.5 py-1.5 border border-white/20 transition-colors"
                >
                  MEMORIA 2024 PDF
                </a>
              </div>
            </div>

            {/* Tarjeta derecha con título de sección */}
            <div className="hidden md:block bg-black/65 backdrop-blur-md border-l-4 border-[#6aa43a] p-4 max-w-md rounded-r-sm shadow-lg">
              <div className="text-[10px] uppercase tracking-[0.16em] text-[#7cc142] font-semibold mb-1">
                {migas}
              </div>
              <h1 className="text-lg sm:text-xl font-serif font-bold text-white leading-snug">
                {titulo}
              </h1>
              <p className="text-xs text-white/85 mt-1 leading-relaxed">
                {subtitulo ||
                  'Convocatorias reales de reforestación en España filtradas según los Estatutos y capacidad técnica de Reforesta.'}
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={prevSlide}
          aria-label="Imagen anterior"
          className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-black/50 hover:bg-[#6aa43a] text-white flex items-center justify-center transition-colors cursor-pointer border border-white/20"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
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
              onClick={() => setActiveIndex(idx)}
              aria-label={`Ir a imagen ${idx + 1}`}
              className={`h-2 transition-all cursor-pointer rounded-full ${
                idx === activeIndex ? 'w-6 bg-[#6aa43a]' : 'w-2 bg-white/50 hover:bg-white/90'
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
  const en30 = aptas.filter((c) => c.diasRestantes <= 30);
  const altoEncaje = aptas.filter((c) => c.matchingGlobal >= 75);
  const fondos = altoEncaje.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const descartadas = Math.max(0, detectadas - aptas.length);
  const horasAhorradas = descartadas * HORAS_LECTURA_POR_CONVOCATORIA;

  const pasos = [
    {
      n: detectadas,
      etiqueta: 'Escaneadas en fuentes',
      nota: real ? 'BDNS, BOE, EU, CCAA y fundaciones' : 'convocatorias verificadas en España',
    },
    {
      n: aptas.length,
      etiqueta: 'Aptas para Reforesta',
      nota: 'cumplen NIF G80428204 y fines',
    },
    {
      n: en30.length,
      etiqueta: 'Cierran en ≤ 30 días',
      nota: 'prioridad de presentación',
    },
    {
      n: altoEncaje.length,
      etiqueta: 'Encaje ≥ 75%',
      nota: fondos > 0 ? `${formatoEuros(fondos)} máx. acumulado` : 'sin importe fijo en bases',
    },
  ];

  return (
    <section className="bg-white border-b border-zinc-200">
      <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <ol className="grid grid-cols-2 lg:grid-cols-4 gap-y-5">
          {pasos.map((p, i) => (
            <li
              key={p.etiqueta}
              className={`px-5 ${i > 0 ? 'lg:border-l border-zinc-200' : ''} ${
                i % 2 === 1 ? 'border-l border-zinc-200 lg:border-l' : ''
              }`}
            >
              <span
                className={`font-serif text-3xl sm:text-4xl font-bold tabular-nums ${
                  i === pasos.length - 1 ? 'text-[#6aa43a]' : 'text-zinc-900'
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
