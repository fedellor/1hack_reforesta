'use client';

import React, { useState } from 'react';
import {
  X,
  ExternalLink,
  FileDown,
  Check,
  Copy,
} from 'lucide-react';
import { Convocatoria, EstadoInterno } from '@/types/convocatoria';
import { esCitaLiteral, limpiarJustificacion } from '@/lib/texto';

interface ConvocatoriaDrawerProps {
  convocatoria: Convocatoria | null;
  onClose: () => void;
  onCambiarEstado?: (id: string, nuevoEstado: EstadoInterno) => void;
}

export function ConvocatoriaDrawer({
  convocatoria,
  onClose,
  onCambiarEstado,
}: ConvocatoriaDrawerProps) {
  const [copiado, setCopiado] = useState(false);

  if (!convocatoria) return null;
  const c = convocatoria;

  const handleCopiarMarkdown = () => {
    const md = `FICHA DE CONVOCATORIA: ${c.titulo}
Organismo: ${c.organismo} (${c.codigoOficial})
Ámbito: ${c.ambitoTerritorial}${c.orografiaPendiente ? ` · ${c.orografiaPendiente}` : ''}
Cuantía máx: ${new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(c.cuantiaMaximaProyecto)} (${c.porcentajeCofinanciacion === 0 ? '100% financiado' : `${c.porcentajeCofinanciacion}% cofinanciación`})
Cierre: ${c.diasRestantes >= 9999 ? 'plazo abierto, sin fecha fijada' : `${c.fechaCierre} (${c.diasRestantes >= 9999 ? 'Plazo abierto' : `${c.diasRestantes} días`} restantes)`}
Elegibilidad: ${c.motivoElegibilidad}
Afinidad Reforesta: ${c.matchingGlobal}% (Restauración: ${c.matchingLineas.restauracionEcosistemas}%, Hábitats: ${c.matchingLineas.conservacionHabitats}%, Educación: ${c.matchingLineas.educacionAmbiental}%)

Resumen de las bases:
${c.resumenEjecutivo}

Acciones financiables:
${c.accionesSubvencionables.map((a) => ` - ${a}`).join('\n')}

Enlace oficial: ${c.urlBasesPdf}`;

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
                  {c.diasRestantes >= 9999 ? 'Plazo abierto (según bases)' : `Cierre: ${new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}`}
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

            {/* 2. Condiciones Económicas */}
            <div className="grid grid-cols-3 gap-3 border border-zinc-200 rounded-none p-3 bg-zinc-50/50">
              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">Cuantía Máx.</span>
                <span className="text-sm font-bold text-zinc-900">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </span>
                <span className="text-[11px] text-zinc-500 block">por proyecto</span>
              </div>

              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">Cofinanciación</span>
                <span className="text-sm font-bold text-zinc-900">
                  {c.porcentajeCofinanciacion === 0 ? '0%' : `${c.porcentajeCofinanciacion}%`}
                </span>
                <span className="text-[11px] text-zinc-500 block">
                  {c.porcentajeCofinanciacion === 0 ? '100% subvencionado' : 'fondos propios'}
                </span>
              </div>

              <div>
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block">Plazo Restante</span>
                <span className="text-sm font-bold text-zinc-900">
                  {c.diasRestantes} días
                </span>
                <span className="text-[11px] text-zinc-500 block">Modalidad: {c.modalidadPago}</span>
              </div>
            </div>

            {/* Orografía y Pendiente */}
            {c.orografiaPendiente && (
              <div className="border border-zinc-200 rounded-none p-3 bg-white">
                <span className="text-[11px] uppercase font-semibold text-zinc-400 block mb-0.5">Orografía y Pendiente del Terreno</span>
                <span className="text-xs font-medium text-zinc-800">{c.orografiaPendiente}</span>
              </div>
            )}

            {/* 3. Resumen Ejecutivo */}
            <div>
              <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1.5">
                Resumen de las Bases
              </h4>
              <p className="bg-zinc-50 border border-zinc-200 rounded-none p-3 leading-relaxed text-zinc-800">
                {c.resumenEjecutivo}
              </p>
            </div>

            {/* 4. Afinidad con las Líneas de Reforesta */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider">
                  Afinidad Temática
                </h4>
                <span className="font-bold text-zinc-900">{c.matchingGlobal}%</span>
              </div>

              <div className="space-y-2 border border-zinc-200 rounded-none p-3 bg-white">
                <div>
                  <div className="flex items-center justify-between text-zinc-700 mb-1">
                    <span>Restauración vegetal y suelos</span>
                    <span className="font-mono">{c.matchingLineas.restauracionEcosistemas}%</span>
                  </div>
                  <div className="w-full bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-700 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.restauracionEcosistemas}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-zinc-700 mb-1">
                    <span>Hábitats, anfibios y fauna</span>
                    <span className="font-mono">{c.matchingLineas.conservacionHabitats}%</span>
                  </div>
                  <div className="w-full bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-700 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.conservacionHabitats}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-zinc-700 mb-1">
                    <span>Educación ambiental y voluntariado</span>
                    <span className="font-mono">{c.matchingLineas.educacionAmbiental}%</span>
                  </div>
                  <div className="w-full bg-zinc-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-700 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.educacionAmbiental}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

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

            {/* 6. Partidas Financiables vs Excluidas */}
            <div className="space-y-3">
              <div>
                <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1">
                  Gastos Subvencionables
                </h4>
                <ul className="space-y-1">
                  {c.accionesSubvencionables.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-zinc-700">
                      <span className="text-emerald-700 font-bold shrink-0">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {c.gastosNoSubvencionables && c.gastosNoSubvencionables.length > 0 && (
                <div>
                  <h4 className="text-xs uppercase font-semibold text-zinc-500 tracking-wider mb-1">
                    Gastos Excluidos
                  </h4>
                  <ul className="space-y-1">
                    {c.gastosNoSubvencionables.map((g, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-zinc-500">
                        <span className="text-zinc-400 font-bold shrink-0">✕</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

          </div>

          {/* Footer del Drawer */}
          <div className="p-4 border-t border-zinc-200 bg-zinc-50/60 flex items-center justify-between gap-3 flex-wrap">
            
            {/* Estado Interno del Pipeline */}
            {onCambiarEstado && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-zinc-500 font-medium">Estado:</span>
                <select
                  value={c.estadoInterno}
                  onChange={(e) => onCambiarEstado(c.id, e.target.value as EstadoInterno)}
                  className="px-2 py-1 rounded border border-zinc-200 bg-white text-zinc-800 text-xs font-medium focus:outline-hidden focus:border-zinc-400 shadow-2xs"
                >
                  <option value="nueva">Nueva</option>
                  <option value="priorizada">Priorizada</option>
                  <option value="en_preparacion">En preparación</option>
                  <option value="presentada">Presentada</option>
                  <option value="descartada">Descartada</option>
                </select>
              </div>
            )}

            {/* Enlaces Oficiales */}
            <div className="flex items-center gap-2">
              <a
                href={c.urlBasesPdf}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-zinc-200 text-zinc-700 bg-white hover:bg-zinc-50 transition-colors text-xs font-medium shadow-2xs"
              >
                <FileDown className="h-3.5 w-3.5 text-zinc-500" />
                <span>Bases Oficiales (PDF)</span>
              </a>

              <a
                href={c.urlSedeElectronica}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-zinc-900 text-white hover:bg-zinc-800 transition-colors text-xs font-medium shadow-2xs"
              >
                <span>Sede Electrónica</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
