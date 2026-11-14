import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { Bosque } from '@/components/Bosque';

// Dato SIMULADO hasta que el backend (rama back) exponga el total rastreado.
const DETECTADAS_SIMULADO = 214;
const HORAS_LECTURA_POR_CONVOCATORIA = 3; // dato del reto: ~3 h de lectura por convocatoria

export function Embudo({ convocatorias }: { convocatorias: Convocatoria[] }) {
  const detectadas = Math.max(DETECTADAS_SIMULADO, convocatorias.length);
  const aptas = convocatorias.filter((c) => c.elegible);
  const en30 = aptas.filter((c) => c.diasRestantes <= 30);
  const altoEncaje = en30.filter((c) => c.matchingGlobal >= 80);
  const fondos30 = altoEncaje.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
  const horasAhorradas = (detectadas - aptas.length) * HORAS_LECTURA_POR_CONVOCATORIA;

  const pasos = [
    { n: detectadas, etiqueta: 'Detectadas', nota: 'en BDNS, boletines y RSC*' },
    { n: aptas.length, etiqueta: 'Aptas para Reforesta', nota: 'sin cláusulas excluyentes' },
    { n: en30.length, etiqueta: 'Cierran en 30 días', nota: 'ventana de decisión' },
    { n: altoEncaje.length, etiqueta: 'Encaje ≥ 80%', nota: `${formatoEuros(fondos30)} en juego` },
  ];

  return (
      <section className="bg-white border-b border-zinc-200">
        <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <ol className="grid grid-cols-2 lg:grid-cols-4 gap-y-8">
            {pasos.map((p, i) => (
              <li key={p.etiqueta} className={`px-6 ${i > 0 ? 'lg:border-l border-zinc-200' : ''} ${i % 2 === 1 ? 'border-l border-zinc-200 lg:border-l' : ''}`}>
                <span className={`font-serif text-5xl font-bold ${i === pasos.length - 1 ? 'text-brand' : 'text-zinc-900'}`}>{p.n}</span>
                <span className="block mt-2 text-sm font-bold uppercase tracking-wide text-zinc-900">{p.etiqueta}</span>
                <span className="block text-sm text-zinc-500">{p.nota}</span>
              </li>
            ))}
          </ol>
          <p className="mt-8 px-6 text-xs text-zinc-400">
            ≈ {horasAhorradas} h de lectura de bases evitadas ({HORAS_LECTURA_POR_CONVOCATORIA} h por convocatoria descartada). *Total detectado simulado para la demo.
          </p>
        </div>
      </section>
  );
}

export function Hero({ titulo, migas }: { titulo: string; migas: string }) {
  return (
      <section className="relative overflow-hidden text-white bg-gradient-to-b from-[#5b5d4c] via-[#85755a] to-[#a38c62] min-h-[280px]">
        {/* Grano fotográfico */}
        <svg aria-hidden className="absolute inset-0 h-full w-full opacity-25 mix-blend-overlay">
          <filter id="grano"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" /></filter>
          <rect width="100%" height="100%" filter="url(#grano)" />
        </svg>

        {/* Pinos azul marino, como el banner de reforesta.es */}
        <svg aria-hidden className="absolute bottom-0 left-0 w-full h-64 sm:h-80" preserveAspectRatio="none" viewBox="0 0 1440 300">
          <Bosque semilla={7} altura={250} color="#3d5a80" opacidad={0.55} />
          <Bosque semilla={23} altura={210} color="#2b4468" opacidad={0.8} />
          <Bosque semilla={41} altura={150} color="#1f3555" opacidad={0.95} />
        </svg>

        <div className="relative max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 flex items-end justify-between gap-6">
          <h1 className="max-w-3xl text-3xl sm:text-[35px] font-bold leading-[1.08]">
            {titulo}
          </h1>
          <p className="hidden md:block pb-2 font-serif text-base text-white shrink-0">{migas}</p>
        </div>
      </section>
  );
}
