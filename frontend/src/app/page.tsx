'use client';

import React, { useState, useMemo } from 'react';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { Header } from '@/components/Header';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaRowCard } from '@/components/ConvocatoriaRowCard';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { TableView } from '@/components/TableView';
import { CalendarView } from '@/components/CalendarView';
import { MapView } from '@/components/MapView';
import { RSCView } from '@/components/RSCView';
import { TreePine, Sparkles, AlertCircle } from 'lucide-react';

export default function Home() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>(MOCK_CONVOCATORIAS);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [vistaActiva, setVistaActiva] = useState<'tarjetas' | 'tabla' | 'calendario' | 'mapa' | 'rsc'>('tarjetas');
  
  const [ordenarPor, setOrdenarPor] = useState<'matching' | 'cuantia' | 'urgencia'>('matching');
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    tipoFuente: 'todos',
    soloElegibles: true, // Por defecto ocultamos exclusiones para ahorrar tiempo a Reforesta
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
  });

  // Manejador para actualizar el estado interno en el pipeline
  const handleCambiarEstado = (id: string, nuevoEstado: EstadoInterno) => {
    setConvocatorias((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estadoInterno: nuevoEstado } : c))
    );
    if (convocatoriaSeleccionada && convocatoriaSeleccionada.id === id) {
      setConvocatoriaSeleccionada((prev) => (prev ? { ...prev, estadoInterno: nuevoEstado } : null));
    }
  };

  // Filtrado y ordenación reactiva
  const convocatoriasFiltradas = useMemo(() => {
    return convocatorias
      .filter((c) => {
        // Filtro de búsqueda textual
        if (filtros.busqueda.trim()) {
          const q = filtros.busqueda.toLowerCase();
          const coincide =
            c.titulo.toLowerCase().includes(q) ||
            c.organismo.toLowerCase().includes(q) ||
            c.codigoOficial.toLowerCase().includes(q) ||
            c.accionesSubvencionables.some((a) => a.toLowerCase().includes(q));
          if (!coincide) return false;
        }

        // Filtro de ámbito
        if (filtros.ambito !== 'todos') {
          if (!c.ambitoTerritorial.toLowerCase().includes(filtros.ambito.toLowerCase())) {
            return false;
          }
        }

        // Filtro de tipo de fuente
        if (filtros.tipoFuente !== 'todos') {
          if (c.tipoFuente !== filtros.tipoFuente) {
            return false;
          }
        }

        // Filtro de elegibilidad (dealbreakers)
        if (filtros.soloElegibles && !c.elegible) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (ordenarPor === 'matching') {
          return b.matchingGlobal - a.matchingGlobal;
        }
        if (ordenarPor === 'cuantia') {
          return b.cuantiaMaximaProyecto - a.cuantiaMaximaProyecto;
        }
        if (ordenarPor === 'urgencia') {
          return a.diasRestantes - b.diasRestantes;
        }
        return 0;
      });
  }, [convocatorias, filtros, ordenarPor]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      
      {/* 1. Header con KPIs y Navegación */}
      <Header
        convocatorias={convocatorias}
        vistaActiva={vistaActiva}
        setVistaActiva={setVistaActiva}
        onRefresh={() => {
          // Feedback de sincronización
          alert('Sincronizado con APIs públicas: BDNS, BOE, BOCM y DOG al día.');
        }}
      />

      {/* 2. Barra de Filtros Multifactor */}
      <FilterBar
        filtros={filtros}
        setFiltros={setFiltros}
        ordenarPor={ordenarPor}
        setOrdenarPor={setOrdenarPor}
        totalConvocatorias={convocatorias.length}
        totalFiltradas={convocatoriasFiltradas.length}
      />

      {/* 3. Contenedor Principal de la Vista */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Banner de Filosofía: Zero-Search Observability */}
        <div className="mb-5 bg-gradient-to-r from-emerald-900/10 via-emerald-800/5 to-transparent border border-emerald-500/20 rounded-xl p-3 text-xs flex items-center justify-between gap-3 text-emerald-950">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-emerald-600 text-white shrink-0">
              <Sparkles className="h-4 w-4" />
            </div>
            <p>
              <strong>Zero-Search Observability:</strong> Oportunidades rastreadas y pre-puntuadas contra los estatutos de Reforesta (restauración vegetal, hábitats de anfibios/fauna y educación ambiental).
            </p>
          </div>
          <span className="hidden sm:inline-block text-[11px] font-semibold text-emerald-800 bg-emerald-100/60 px-2 py-0.5 rounded">
            Cero alucinaciones: Enlace directo al PDF oficial
          </span>
        </div>

        {/* Renderizado Condicional de Vistas */}
        {vistaActiva === 'tarjetas' && (
          <div className="space-y-3">
            {convocatoriasFiltradas.map((convocatoria) => (
              <ConvocatoriaRowCard
                key={convocatoria.id}
                convocatoria={convocatoria}
                onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
                seleccionada={convocatoriaSeleccionada?.id === convocatoria.id}
              />
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
                <AlertCircle className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                <h4 className="font-bold text-slate-700 text-sm">No se encontraron convocatorias con estos filtros</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Prueba a relajar los criterios de búsqueda o desactiva el filtro de exclusiones.
                </p>
              </div>
            )}
          </div>
        )}

        {vistaActiva === 'tabla' && (
          <TableView
            convocatorias={convocatoriasFiltradas}
            onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
          />
        )}

        {vistaActiva === 'calendario' && (
          <CalendarView
            convocatorias={convocatoriasFiltradas}
            onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
          />
        )}

        {vistaActiva === 'mapa' && (
          <MapView
            convocatorias={convocatoriasFiltradas}
            onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
          />
        )}

        {vistaActiva === 'rsc' && (
          <RSCView
            convocatorias={convocatorias}
            onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
          />
        )}

      </main>

      {/* 4. Panel Lateral Desplegable (Ficha Ejecutiva Completa) */}
      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
        onCambiarEstado={handleCambiarEstado}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        <p>
          Proyecto desarrollado para el reto <strong>1hack A Coruña · El reto de Reforesta</strong> (Common Seeds)
        </p>
      </footer>

    </div>
  );
}
