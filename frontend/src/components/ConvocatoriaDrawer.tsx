'use client';

import React from 'react';
import {
  X,
  ExternalLink,
  FileDown,
  Calendar,
  Euro,
  MapPin,
  Building2,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  HelpCircle,
  TreePine,
  Fish,
  Users,
  Sparkles,
  Share2,
  Check,
} from 'lucide-react';
import { Convocatoria, EstadoInterno } from '@/types/convocatoria';

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
  if (!convocatoria) return null;
  const c = convocatoria;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
      />

      {/* Drawer Panel */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-2xl flex flex-col">
          
          {/* Header del Drawer */}
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1 text-xs">
                <span className="font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-800 font-semibold">
                  {c.codigoOficial}
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">
                  {c.ambitoTerritorial}
                </span>
                <span className="text-slate-500 font-medium">
                  Cierre: {new Date(c.fechaCierre).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })}
                </span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 leading-snug">
                {c.titulo}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 font-medium">{c.organismo}</p>
            </div>
            
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Contenido con Scroll */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-700">
            
            {/* 1. Semáforo de Elegibilidad */}
            <div
              className={`p-4 rounded-xl border ${
                c.elegible
                  ? 'bg-emerald-50/70 border-emerald-200'
                  : 'bg-rose-50/70 border-rose-200'
              }`}
            >
              <div className="flex items-start gap-3">
                {c.elegible ? (
                  <ShieldCheck className="h-6 w-6 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <ShieldAlert className="h-6 w-6 text-rose-600 shrink-0 mt-0.5" />
                )}
                <div className="space-y-1">
                  <h4 className={`font-bold ${c.elegible ? 'text-emerald-900' : 'text-rose-900'}`}>
                    {c.elegible ? '🟢 Convocatoria Apta para Reforesta' : '🔴 Convocatoria No Apta (Exclusión Legal)'}
                  </h4>
                  <p className="text-xs text-slate-700">{c.motivoElegibilidad}</p>
                  {c.dealbreakers.length > 0 && (
                    <ul className="mt-2 text-xs space-y-1 text-rose-800 list-disc list-inside">
                      {c.dealbreakers.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            {/* 2. KPIs Económicos y Plazo */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                <p className="text-[11px] font-semibold text-slate-500 uppercase">Cuantía Máxima</p>
                <p className="text-lg font-black text-slate-900 mt-0.5">
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                    c.cuantiaMaximaProyecto
                  )}
                </p>
                <span className="text-[10px] text-slate-500">por proyecto</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                <p className="text-[11px] font-semibold text-slate-500 uppercase">Cofinanciación</p>
                <p className="text-lg font-black text-emerald-700 mt-0.5">
                  {c.porcentajeCofinanciacion === 0 ? '100%' : `${100 - c.porcentajeCofinanciacion}%`}
                </p>
                <span className="text-[10px] text-slate-500">
                  {c.porcentajeCofinanciacion === 0 ? 'Subvencionado' : `Exige ${c.porcentajeCofinanciacion}% propio`}
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                <p className="text-[11px] font-semibold text-slate-500 uppercase">Plazo Restante</p>
                <p
                  className={`text-lg font-black mt-0.5 ${
                    c.diasRestantes <= 7 ? 'text-rose-600' : c.diasRestantes <= 20 ? 'text-amber-600' : 'text-slate-900'
                  }`}
                >
                  {c.diasRestantes} días
                </p>
                <span className="text-[10px] text-slate-500">Modalidad: {c.modalidadPago}</span>
              </div>
            </div>

            {/* 3. Resumen Ejecutivo (Lenguaje Llano) */}
            <div>
              <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                Resumen Ejecutivo Analítico
              </h3>
              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs leading-relaxed text-slate-800">
                {c.resumenEjecutivo}
              </div>
            </div>

            {/* 4. Matching Semántico Desglosado */}
            <div>
              <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-2">
                <TreePine className="h-4 w-4 text-emerald-600" />
                Afinidad con las 3 Líneas de Reforesta ({c.matchingGlobal}%)
              </h3>
              <div className="grid grid-cols-3 gap-2">
                
                <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-emerald-900 mb-1">
                    <span>Rest. Vegetal</span>
                    <span>{c.matchingLineas.restauracionEcosistemas}%</span>
                  </div>
                  <div className="w-full bg-emerald-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-600 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.restauracionEcosistemas}%` }}
                    />
                  </div>
                </div>

                <div className="bg-blue-50/60 border border-blue-200 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-blue-900 mb-1">
                    <span>Hábitats/Fauna</span>
                    <span>{c.matchingLineas.conservacionHabitats}%</span>
                  </div>
                  <div className="w-full bg-blue-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.conservacionHabitats}%` }}
                    />
                  </div>
                </div>

                <div className="bg-amber-50/60 border border-amber-200 rounded-lg p-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-amber-900 mb-1">
                    <span>Educación</span>
                    <span>{c.matchingLineas.educacionAmbiental}%</span>
                  </div>
                  <div className="w-full bg-amber-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-amber-600 h-1.5 rounded-full"
                      style={{ width: `${c.matchingLineas.educacionAmbiental}%` }}
                    />
                  </div>
                </div>

              </div>
            </div>

            {/* 5. Citas Textuales Literales de las Bases */}
            {c.citasBasesJustificacion.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-2 text-xs">
                  📜 Citas Literales de las Bases Oficiales (Anti-Alucinación)
                </h3>
                <div className="space-y-2">
                  {c.citasBasesJustificacion.map((cita, i) => (
                    <blockquote
                      key={i}
                      className="text-xs bg-slate-50 border-l-3 border-emerald-500 pl-3 py-1.5 text-slate-700 italic rounded-r"
                    >
                      &ldquo;{cita}&rdquo;
                    </blockquote>
                  ))}
                </div>
              </div>
            )}

            {/* 6. Acciones Subvencionables y Gastos Excluidos */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Acciones Subvencionables */}
              <div className="space-y-2">
                <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Acciones Financiables
                </h4>
                <ul className="text-xs space-y-1.5">
                  {c.accionesSubvencionables.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-slate-700">
                      <span className="text-emerald-500 font-bold shrink-0">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Gastos Excluidos */}
              {c.gastosNoSubvencionables && c.gastosNoSubvencionables.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
                    <XCircle className="h-4 w-4 text-rose-600" />
                    Gastos Excluidos
                  </h4>
                  <ul className="text-xs space-y-1.5">
                    {c.gastosNoSubvencionables.map((g, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-slate-600">
                        <span className="text-rose-500 font-bold shrink-0">✕</span>
                        <span>{g}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            </div>

            {/* 7. Requisitos de Solvencia */}
            {c.requisitosSolvencia && c.requisitosSolvencia.length > 0 && (
              <div>
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-600 flex items-center gap-1.5 mb-1.5">
                  <HelpCircle className="h-4 w-4 text-slate-500" />
                  Requisitos de Solvencia Exigidos
                </h4>
                <ul className="text-xs space-y-1 text-slate-700 list-disc list-inside bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  {c.requisitosSolvencia.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

          </div>

          {/* Footer del Drawer con Enlaces Oficiales y Estado Interno */}
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3 flex-wrap">
            
            {/* Selector de Estado Interno */}
            {onCambiarEstado && (
              <div className="flex items-center gap-2 text-xs">
                <span className="font-semibold text-slate-600">Estado equipo:</span>
                <select
                  value={c.estadoInterno}
                  onChange={(e) => onCambiarEstado(c.id, e.target.value as EstadoInterno)}
                  className="px-2.5 py-1 rounded-md border border-slate-300 font-semibold bg-white text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="nueva">⚪ Nueva</option>
                  <option value="priorizada">⭐ Priorizada</option>
                  <option value="en_preparacion">✏️ En preparación</option>
                  <option value="presentada">✅ Presentada</option>
                  <option value="descartada">❌ Descartada</option>
                </select>
              </div>
            )}

            {/* Botones Enlaces Oficiales */}
            <div className="flex items-center gap-2">
              <a
                href={c.urlBasesPdf}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs"
              >
                <FileDown className="h-3.5 w-3.5 text-slate-500" />
                <span>Bases PDF</span>
              </a>

              <a
                href={c.urlSedeElectronica}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-xs"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span>Sede Electrónica</span>
              </a>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
