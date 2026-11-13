'use client';

import React from 'react';
import {
  Calendar,
  Euro,
  FileText,
  MapPin,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Building2,
  TreePine,
  Fish,
  Users,
} from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';

interface ConvocatoriaRowCardProps {
  convocatoria: Convocatoria;
  onSeleccionar: (convocatoria: Convocatoria) => void;
  seleccionada?: boolean;
}

export function ConvocatoriaRowCard({
  convocatoria,
  onSeleccionar,
  seleccionada,
}: ConvocatoriaRowCardProps) {
  const c = convocatoria;

  const getUrgenciaBadge = (urgencia: string, dias: number) => {
    if (dias <= 7) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">
          <Calendar className="h-3 w-3" />
          ¡Cierre en {dias} días!
        </span>
      );
    }
    if (dias <= 20) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          <Calendar className="h-3 w-3" />
          Cierra en {dias} días
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
        <Calendar className="h-3 w-3" />
        {dias} días restantes
      </span>
    );
  };

  const getFuenteBadge = (fuente: string) => {
    switch (fuente) {
      case 'publica_estatal':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            🏛️ Estatal (MITECO)
          </span>
        );
      case 'publica_autonomica':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            📜 Autonómica (Boletín CCAA)
          </span>
        );
      case 'privada_rsc':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            🏢 Mecenazgo RSC Privado
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
            Pública
          </span>
        );
    }
  };

  return (
    <div
      onClick={() => onSeleccionar(c)}
      className={`group relative rounded-xl border p-4 transition-all duration-200 cursor-pointer bg-white ${
        seleccionada
          ? 'border-emerald-500 ring-2 ring-emerald-500/30 shadow-md bg-emerald-50/20'
          : 'border-slate-200 hover:border-emerald-400 hover:shadow-md'
      } ${!c.elegible ? 'opacity-70 bg-slate-50/70 border-dashed border-rose-200' : ''}`}
    >
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        
        {/* Columna Izquierda: Información Principal */}
        <div className="flex-1 space-y-2">
          
          {/* Etiquetas Superiores */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            {getFuenteBadge(c.tipoFuente)}
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
              <MapPin className="h-3 w-3 text-slate-400" />
              {c.ambitoTerritorial}
            </span>
            <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
              {c.codigoOficial}
            </span>
            {getUrgenciaBadge(c.urgencia, c.diasRestantes)}
          </div>

          {/* Título de la Convocatoria */}
          <div>
            <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors line-clamp-2">
              {c.titulo}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1 font-medium">
              <span>{c.organismo}</span>
            </p>
          </div>

          {/* Cita Textual Clave Extraída por LLM */}
          {c.citasBasesJustificacion.length > 0 && (
            <div className="bg-slate-50 border-l-2 border-emerald-500 px-2.5 py-1.5 rounded-r text-xs text-slate-700 italic">
              <span className="font-semibold text-emerald-800 not-italic mr-1">Extracción oficial:</span>
              &ldquo;{c.citasBasesJustificacion[0]}&rdquo;
            </div>
          )}

          {/* Semáforo de Elegibilidad */}
          <div className="flex items-center gap-2 pt-1 text-xs">
            {c.elegible ? (
              <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                {c.motivoElegibilidad}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-rose-700 font-semibold bg-rose-50 px-2 py-0.5 rounded">
                <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
                {c.motivoElegibilidad}
              </span>
            )}
          </div>

        </div>

        {/* Columna Derecha: Scoring Semántico y Finanzas */}
        <div className="flex lg:flex-col items-center lg:items-end justify-between gap-3 border-t lg:border-t-0 lg:border-l border-slate-100 pt-3 lg:pt-0 lg:pl-5 shrink-0">
          
          {/* Tarjeta de Finanzas */}
          <div className="text-left lg:text-right">
            <div className="flex items-center lg:justify-end gap-1 text-slate-500 text-[11px] font-medium">
              <Euro className="h-3 w-3" />
              <span>Cuantía Máx.</span>
            </div>
            <p className="text-lg font-black text-slate-900">
              {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(
                c.cuantiaMaximaProyecto
              )}
            </p>
            <p className="text-[11px] font-medium text-emerald-700">
              {c.porcentajeCofinanciacion === 0
                ? '🟢 100% subvencionable (0% propio)'
                : `⚠️ Requiere ${c.porcentajeCofinanciacion}% cofinanciación`}
            </p>
          </div>

          {/* Score Reforesta y Micro-barras */}
          <div className="w-48 bg-slate-50 border border-slate-200/80 rounded-lg p-2 text-xs">
            
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-emerald-600" /> Match Reforesta
              </span>
              <span
                className={`font-black text-sm px-1.5 py-0.2 rounded ${
                  c.matchingGlobal >= 90
                    ? 'bg-emerald-500 text-white'
                    : c.matchingGlobal >= 80
                    ? 'bg-emerald-100 text-emerald-900'
                    : 'bg-slate-200 text-slate-700'
                }`}
              >
                {c.matchingGlobal}%
              </span>
            </div>

            {/* Barras de las 3 Líneas */}
            <div className="space-y-1 text-[10px]">
              
              <div className="flex items-center justify-between">
                <span className="text-slate-600 flex items-center gap-1 truncate">
                  <TreePine className="h-2.5 w-2.5 text-emerald-600" /> Rest. Vegetal
                </span>
                <span className="font-semibold text-slate-700">{c.matchingLineas.restauracionEcosistemas}%</span>
              </div>
              <div className="w-full bg-slate-200 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-1 rounded-full"
                  style={{ width: `${c.matchingLineas.restauracionEcosistemas}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 flex items-center gap-1 truncate">
                  <Fish className="h-2.5 w-2.5 text-blue-600" /> Hábitats / Fauna
                </span>
                <span className="font-semibold text-slate-700">{c.matchingLineas.conservacionHabitats}%</span>
              </div>
              <div className="w-full bg-slate-200 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-blue-500 h-1 rounded-full"
                  style={{ width: `${c.matchingLineas.conservacionHabitats}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-600 flex items-center gap-1 truncate">
                  <Users className="h-2.5 w-2.5 text-amber-600" /> Educ. / Volunt.
                </span>
                <span className="font-semibold text-slate-700">{c.matchingLineas.educacionAmbiental}%</span>
              </div>
              <div className="w-full bg-slate-200 h-1 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-1 rounded-full"
                  style={{ width: `${c.matchingLineas.educacionAmbiental}%` }}
                />
              </div>

            </div>

          </div>

          {/* Botón de Ficha Ejecutiva */}
          <div className="hidden lg:flex items-center gap-1 text-xs font-semibold text-emerald-700 group-hover:translate-x-1 transition-transform">
            <span>Ver Ficha Ejecutiva</span>
            <ChevronRight className="h-4 w-4" />
          </div>

        </div>

      </div>
    </div>
  );
}
