'use client';

import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { EmbudoReal } from '@/services/api';
import { formatoEuros } from '@/lib/territorio';
import { plazoSinFijar } from '@/lib/plazo';

interface HeroProps {
  titulo: string;
  migas: string;
}

/** Franja de título con la imagen de cabecera de reforesta.es. Fina a propósito: el contenido va en primer plano. */
export function Hero({ titulo, migas }: HeroProps) {
  return (
    <div className="relative bg-[#1b2c1f] text-white overflow-hidden">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/reforesta/reforesta-slider-01.jpg" alt="" className="absolute inset-0 h-full w-full object-cover object-center" />
      <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/60 to-black/40" />
      <div className="relative max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <p className="text-[11px] uppercase tracking-[0.18em] text-white/70">{migas}</p>
        <h1 className="mt-1 font-serif text-2xl sm:text-3xl font-bold leading-tight">{titulo}</h1>
      </div>
    </div>
  );
}

// Dato SIMULADO hasta que el backend (rama back) exponga el total rastreado.
const DETECTADAS_SIMULADO = 214;
const HORAS_LECTURA_POR_CONVOCATORIA = 3; // dato del reto: ~3 h de lectura por convocatoria

export function Embudo({ convocatorias, embudo }: { convocatorias: Convocatoria[]; embudo: EmbudoReal | null }) {
  const real = embudo !== null && embudo.detectadas > 0;
  const detectadas = real ? Math.max(embudo.detectadas, convocatorias.length) : Math.max(DETECTADAS_SIMULADO, convocatorias.length);
  const aptas = convocatorias.filter((c) => c.elegible);
  const en30 = aptas.filter((c) => !plazoSinFijar(c) && c.diasRestantes <= 30);
  const altoEncaje = en30.filter((c) => c.matchingGlobal >= 80);
  const fondos30 = altoEncaje.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const horasAhorradas = (detectadas - aptas.length) * HORAS_LECTURA_POR_CONVOCATORIA;

  const pasos = [
    { n: detectadas, etiqueta: 'Detectadas', nota: real ? 'en la última ingesta del radar' : 'en BDNS, boletines y RSC*' },
    { n: aptas.length, etiqueta: 'Aptas para Reforesta', nota: 'sin cláusulas excluyentes' },
    { n: en30.length, etiqueta: 'Cierran en 30 días', nota: 'ventana de decisión' },
    { n: altoEncaje.length, etiqueta: 'Encaje ≥ 80%', nota: `${formatoEuros(fondos30)} en juego` },
  ];

  return (
      <section className="bg-white border-b border-zinc-200">
        <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <ol className="grid grid-cols-2 lg:grid-cols-4 gap-y-4">
            {pasos.map((p, i) => (
              <li key={p.etiqueta} className={`px-4 ${i > 0 ? 'lg:border-l border-zinc-200' : ''} ${i % 2 === 1 ? 'border-l border-zinc-200 lg:border-l' : ''}`}>
                <span className={`font-serif text-3xl font-bold ${i === pasos.length - 1 ? 'text-brand' : 'text-zinc-900'}`}>{p.n}</span>
                <span className="block text-xs font-bold uppercase tracking-wide text-zinc-900">{p.etiqueta}</span>
                <span className="block text-xs text-zinc-500">{p.nota}</span>
              </li>
            ))}
          </ol>
          <p className="mt-3 px-4 text-xs text-zinc-400">
            ≈ {horasAhorradas} h de lectura de bases evitadas ({HORAS_LECTURA_POR_CONVOCATORIA} h por convocatoria descartada). {real ? '' : '*Total detectado simulado: el radar no está conectado.'}
          </p>
        </div>
      </section>
  );
}

