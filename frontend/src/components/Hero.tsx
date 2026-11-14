import React from 'react';
import { Convocatoria } from '@/types/convocatoria';
import { formatoEuros } from '@/lib/territorio';
import { Bosque } from '@/components/Bosque';

// Dato SIMULADO hasta que el backend (rama back) exponga el total rastreado.
const DETECTADAS_SIMULADO = 214;
const HORAS_LECTURA_POR_CONVOCATORIA = 3; // dato del reto: ~3 h de lectura por convocatoria

export function Hero({ convocatorias }: { convocatorias: Convocatoria[] }) {
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
    <section className="relative overflow-hidden text-white bg-gradient-to-b from-[#5b5d4c] via-[#85755a] to-[#a38c62]">
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

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-24 sm:pb-28">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/80">Próximos 30 días</p>
        <h1 className="mt-2 max-w-3xl text-3xl sm:text-4xl font-bold leading-tight drop-shadow-sm">
          Estas son las convocatorias a las que Reforesta puede presentarse este mes
        </h1>

        {/* Embudo: de todo lo que existe a lo que merece una decisión */}
        <ol className="mt-7 grid grid-cols-2 lg:grid-cols-4 gap-3 max-w-4xl">
          {pasos.map((p, i) => (
            <li
              key={p.etiqueta}
              className={`relative rounded-md border px-4 py-3 backdrop-blur-sm ${
                i === pasos.length - 1 ? 'border-brand bg-[#141414]/70' : 'border-white/20 bg-[#141414]/45'
              }`}
            >
              <span className={`font-serif text-2xl sm:text-3xl font-bold ${i === pasos.length - 1 ? 'text-brand-light' : ''}`}>{p.n}</span>
              <span className="block text-[11px] uppercase tracking-wider text-white/85 mt-0.5">{p.etiqueta}</span>
              <span className="block text-[11px] text-white/60">{p.nota}</span>
              {i < pasos.length - 1 && <span aria-hidden className="hidden lg:block absolute -right-2.5 top-1/2 -translate-y-1/2 text-white/60">›</span>}
            </li>
          ))}
        </ol>
        <p className="mt-3 text-[11px] text-white/75">
          ≈ {horasAhorradas} h de lectura de bases evitadas ({HORAS_LECTURA_POR_CONVOCATORIA} h por convocatoria descartada). *Total detectado simulado para la demo.
        </p>
      </div>

      {/* Migas, como en reforesta.es */}
      <p className="hidden md:block absolute right-8 top-10 font-serif text-sm text-white/90">Reforesta / Radar</p>
    </section>
  );
}
