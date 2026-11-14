import React from 'react';

/** Silueta de pinos generada de forma determinista (sin imágenes externas). Se dibuja en un viewBox 1440×300. */
export function Bosque({ semilla, altura, color, opacidad }: { semilla: number; altura: number; color: string; opacidad: number }) {
  const trazo: string[] = [];
  let x = -40;
  let i = semilla;
  const base = 300;
  while (x < 1480) {
    i = (i * 9301 + 49297) % 233280;
    const r = i / 233280;
    const h = altura * (0.5 + r * 0.5);
    const w = h * 0.42;
    const cx = x + w / 2;
    // Pino de copa irregular: 4 pisos escalonados + tronco
    const pisos = 4;
    let d = `M${cx} ${base - h}`;
    for (let p = 1; p <= pisos; p++) {
      const y = base - h + (h * 0.82 * p) / pisos;
      const ancho = (w / 2) * (p / pisos) * (0.85 + ((i >> p) % 3) * 0.08);
      d += ` L${cx + ancho} ${y} L${cx + ancho * 0.55} ${y - h * 0.02}`;
    }
    d += ` L${cx + w * 0.05} ${base} L${cx - w * 0.05} ${base}`;
    for (let p = pisos; p >= 1; p--) {
      const y = base - h + (h * 0.82 * p) / pisos;
      const ancho = (w / 2) * (p / pisos) * (0.85 + ((i >> (p + 1)) % 3) * 0.08);
      d += ` L${cx - ancho * 0.55} ${y - h * 0.02} L${cx - ancho} ${y}`;
    }
    d += ' Z';
    trazo.push(d);
    x += w * (0.45 + r * 0.4);
  }
  return <path d={trazo.join(' ')} fill={color} fillOpacity={opacidad} />;
}
