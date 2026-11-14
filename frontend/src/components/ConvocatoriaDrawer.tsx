'use client';

import React, { useState } from 'react';
import {
  X,
  Check,
  Copy,
} from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { esLicitacion, textoImporte } from '@/lib/territorio';
import { esCitaLiteral, limpiarJustificacion } from '@/lib/texto';
import { aperturaISO, diasHastaApertura, esProxima } from '@/lib/plazo';

/** Enlace único a la información y las bases: la ficha oficial si apunta a una página concreta; si no, la sede o el PDF de las bases. */
function enlaceOficial(c: Convocatoria): string {
  const concreta = (u?: string) => {
    if (!u) return false;
    try {
      const { pathname } = new URL(u);
      return pathname.replace(/\/+$/, '').length > 1;
    } catch {
      return false;
    }
  };
  return [c.fuenteUrl, c.urlSedeElectronica, c.urlBasesPdf].find(concreta) || c.fuenteUrl || c.urlSedeElectronica || c.urlBasesPdf || '';
}

interface ConvocatoriaDrawerProps {
  convocatoria: Convocatoria | null;
  onClose: () => void;
}

export function ConvocatoriaDrawer({
  convocatoria,
  onClose,
}: ConvocatoriaDrawerProps) {
  const [copiado, setCopiado] = useState(false);

  if (!convocatoria) return null;
  const c = convocatoria;

  const handleCopiarMarkdown = () => {
    const cierre = c.diasRestantes >= 9999 ? 'plazo abierto, sin fecha fijada' : `${c.fechaCierre.slice(0, 10)} (${esProxima(c) ? `abre en ${diasHastaApertura(c)} días` : `${c.diasRestantes} días restantes`})`;
    const concretos = c.accionesSubvencionables[0] !== 'Actuaciones técnicas' ? c.accionesSubvencionables : [];
    const md = `FICHA DE CONVOCATORIA: ${c.titulo}
Organismo: ${c.organismo} (${c.codigoOficial})
Ámbito: ${c.ambitoTerritorial}
${esLicitacion(c) ? 'Importe del contrato' : 'Cuantía máx'}: ${textoImporte(c)}
Cierre: ${cierre}
Elegibilidad: ${c.motivoElegibilidad}
Afinidad Reforesta: ${c.matchingGlobal}% (Restauración: ${c.matchingLineas.restauracionEcosistemas}%, Hábitats: ${c.matchingLineas.conservacionHabitats}%, Educación: ${c.matchingLineas.educacionAmbiental}%)
${c.resumenEjecutivo && !c.resumenEjecutivo.startsWith('Convocatoria promovida por') ? `\nResumen de las bases:\n${c.resumenEjecutivo}\n` : ''}${concretos.length ? `\nGastos subvencionables:\n${concretos.map((a) => ` - ${a}`).join('\n')}\n` : ''}
Enlace oficial: ${enlaceOficial(c)}`;

    navigator.clipboard.writeText(md);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-zinc-900/20 backdrop-blur-2xs transition-opacity"
      />

      {/* Drawer Panel */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white shadow-xl flex flex-col border-l border-zinc-200">
          
          {/* Header del Drawer */}
          <div className="px-6 py-4 border-b border-zinc-200 flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs">
                <span className="font-semibold text-zinc-600 bg-zinc-100 px-2 py-0.5 rounded">
                  {c.codigoOficial}
                </span>
                <span className="text-zinc-400">·</span>
                <span className="text-zinc-600 font-medium">
                  {c.ambitoTerritorial}
                </span>
                <span className="text-zinc-400">·</span>
                <span className="text-zinc-500">
                  {esProxima(c) && aperturaISO(c) ? `Abre el ${new Date(`${aperturaISO(c)}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })} · cierra el ${new Date(`${c.fechaCierre}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}` : c.diasRestantes >= 9999 ? 'Plazo abierto (según bases)' : `Cierre: ${new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}`}
                </span>
              </div>
              <h2 className="text-base font-semibold text-zinc-900 leading-snug">
                {c.titulo}
              </h2>
              <p className="text-xs text-zinc-500">{c.organismo}</p>
            </div>
            
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                onClick={handleCopiarMarkdown}
                title="Copiar resumen en texto"
                className="px-2.5 py-1 rounded border border-zinc-200 text-zinc-700 hover:bg-zinc-50 transition-colors text-xs font-medium flex items-center gap-1"
              >
                {copiado ? <Check className="h-3.5 w-3.5 text-emerald-700" /> : <Copy className="h-3.5 w-3.5 text-zinc-500" />}
                <span>{copiado ? 'Copiado' : 'Copiar'}</span>
              </button>

              <button
                onClick={onClose}
                className="p-1 rounded text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Contenido con Scroll */}
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 text-xs text-zinc-700">
            
            {/* 1. Diagnóstico de Elegibilidad */}
            <div
              className={`p-3.5 rounded-none border ${
                c.elegible
                  ? 'bg-emerald-50/50 border-emerald-200'
                  : 'bg-rose-50/50 border-rose-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`h-2 w-2 rounded-full ${
                    c.elegible ? 'bg-emerald-600' : 'bg-rose-600'
                  }`}
                />
                <span className={`font-semibold text-xs ${c.elegible ? 'text-emerald-900' : 'text-rose-900'}`}>
                  {c.elegible ? 'Convocatoria Apta para Reforesta' : 'Convocatoria Excluida por Bases'}
                </span>
              </div>
              <p className="text-zinc-700 leading-relaxed">{limpiarJustificacion(c.motivoElegibilidad)}</p>
              {c.dealbreakers.length > 0 && (
                <div className={`mt-3 pt-3 border-t ${c.elegible ? 'border-amber-200' : 'border-rose-200'}`}>
                  <p className={`font-semibold mb-1 ${c.elegible ? 'text-amber-800' : 'text-rose-800'}`}>
                    {c.elegible ? 'A tener en cuenta' : 'Motivos de exclusión'}
                  </p>
                  <ul className={`list-disc list-inside space-y-0.5 ${c.elegible ? 'text-amber-900' : 'text-rose-800'}`}>
                    {c.dealbreakers.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* 2. Los tres datos que deciden: importe, plazo y afinidad */}
            <div className="grid grid-cols-3 gap-3 border border-zinc-200 p-3 bg-zinc-50/50">
              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">{esLicitacion(c) ? 'Importe del contrato' : 'Cuantía máx.'}</span>
                <span className="text-sm font-bold text-zinc-900">{textoImporte(c)}</span>
                {!esLicitacion(c) && <span className="text-[11px] text-zinc-500 block">por proyecto</span>}
              </div>
              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">{esProxima(c) ? 'Abre' : 'Cierre'}</span>
                <span className="text-sm font-bold text-zinc-900">
                  {esProxima(c)
                    ? `en ${diasHastaApertura(c)} días`
                    : c.diasRestantes >= 9999
                      ? 'Sin fecha fijada'
                      : new Date(`${c.fechaCierre.slice(0, 10)}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}
                </span>
                <span className="text-[11px] text-zinc-500 block">
                  {esProxima(c) ? `cierra el ${new Date(`${c.fechaCierre.slice(0, 10)}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}` : c.diasRestantes >= 9999 ? 'plazo abierto' : `${c.diasRestantes} días restantes`}
                </span>
              </div>
              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">Afinidad</span>
                <span className="text-sm font-bold text-zinc-900">{c.matchingGlobal}%</span>
                <span className="text-[11px] text-zinc-500 block">
                  Restauración {c.matchingLineas.restauracionEcosistemas}% · Hábitats {c.matchingLineas.conservacionHabitats}% · Educación {c.matchingLineas.educacionAmbiental}%
                </span>
              </div>
            </div>

            {/* 3. Resumen: solo si dice algo que no esté ya arriba (la plantilla automática repite organismo e importe) */}
            {c.resumenEjecutivo && !c.resumenEjecutivo.startsWith('Convocatoria promovida por') && (
              <div>
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1.5">Resumen de las bases</h4>
                <p className="bg-zinc-50 border border-zinc-200 p-3 leading-relaxed text-zinc-800">{c.resumenEjecutivo}</p>
              </div>
            )}

            {/* 5. Citas de las bases (literales) y justificación del radar (generada) */}
            {c.citasBasesJustificacion.some(esCitaLiteral) && (
              <div>
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1.5">
                  Citas Textuales de las Bases
                </h4>
                <div className="space-y-1.5">
                  {c.citasBasesJustificacion.filter(esCitaLiteral).map((cita, i) => (
                    <blockquote key={i} className="bg-zinc-50 border-l-2 border-zinc-800 pl-3 py-1.5 text-zinc-700 italic rounded-r text-xs">
                      &ldquo;{cita}&rdquo;
                    </blockquote>
                  ))}
                </div>
              </div>
            )}
            {c.citasBasesJustificacion.some((t) => !esCitaLiteral(t)) && (
              <div>
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1.5">Por qué lo recomienda el radar</h4>
                <ul className="space-y-1.5 list-disc list-inside text-zinc-700">
                  {c.citasBasesJustificacion.filter((t) => !esCitaLiteral(t)).map((t, i) => (
                    <li key={i}>{limpiarJustificacion(t)}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gastos subvencionables: solo cuando la convocatoria los concreta (la lista genérica se repite en casi todas) */}
            {c.accionesSubvencionables.length > 0 && c.accionesSubvencionables[0] !== 'Actuaciones técnicas' && (
              <div>
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1">Gastos subvencionables</h4>
                <ul className="space-y-1">
                  {c.accionesSubvencionables.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-zinc-700">
                      <span className="text-emerald-700 font-bold shrink-0">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

          </div>

          {/* Footer del Drawer */}
          <div className="p-4 border-t border-zinc-200 bg-zinc-50/60 flex items-center justify-end gap-3 flex-wrap">
            
            {/* Un solo enlace oficial: la ficha con la información y las bases */}
            {enlaceOficial(c) && (
              <a
                href={enlaceOficial(c)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2.5 px-6 py-3 rounded-full bg-brand text-white hover:bg-[#3f6a2c] transition-colors text-sm font-bold uppercase tracking-wide shadow-md"
              >
                <span>Convocatoria oficial</span>
              </a>
            )}

          </div>

        </div>
      </div>
    </div>
  );
}
