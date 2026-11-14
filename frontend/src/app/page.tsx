'use client';

import React, { useState, useMemo } from 'react';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { Header } from '@/components/Header';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaRowCard } from '@/components/ConvocatoriaRowCard';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { TableView } from '@/components/TableView';
import { PipelineView } from '@/components/PipelineView';
import { MapView } from '@/components/MapView';
import { RSCView } from '@/components/RSCView';
import { AlertCircle } from 'lucide-react';

export default function Home() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>(MOCK_CONVOCATORIAS);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [vistaActiva, setVistaActiva] = useState<'tarjetas' | 'tabla' | 'pipeline' | 'mapa' | 'rsc'>('tarjetas');
  
  const [ordenarPor, setOrdenarPor] = useState<'matching' | 'cuantia' | 'urgencia'>('matching');
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    tipoFuente: 'todos',
    soloElegibles: true, // Por defecto ocultamos exclusiones para ahorrar tiempo
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
        // Búsqueda textual
        if (filtros.busqueda.trim()) {
          const q = filtros.busqueda.toLowerCase();
          const coincide =
            c.titulo.toLowerCase().includes(q) ||
            c.organismo.toLowerCase().includes(q) ||
            c.codigoOficial.toLowerCase().includes(q) ||
            (c.orografiaPendiente && c.orografiaPendiente.toLowerCase().includes(q)) ||
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
    <div className="min-h-screen bg-slate-100/60 text-slate-800 flex flex-col font-sans antialiased">
      
      {/* 1. Header con KPIs y Navegación */}
      <Header
        convocatorias={convocatorias}
        vistaActiva={vistaActiva}
        setVistaActiva={setVistaActiva}
        onRefresh={() => {
          alert('Convocatorias sincronizadas con fuentes oficiales (BDNS, BOE y CCAA).');
        }}
      />

      {/* 2. Barra de Filtros */}
      <FilterBar
        filtros={filtros}
        setFiltros={setFiltros}
        ordenarPor={ordenarPor}
        setOrdenarPor={setOrdenarPor}
        totalConvocatorias={convocatorias.length}
        totalFiltradas={convocatoriasFiltradas.length}
      />

      {/* 3. Contenedor Principal */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5">
        
        {/* Renderizado Condicional de Vistas */}
        {vistaActiva === 'tarjetas' && (
          <div className="space-y-2.5">
            {convocatoriasFiltradas.map((convocatoria) => (
              <ConvocatoriaRowCard
                key={convocatoria.id}
                convocatoria={convocatoria}
                onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
                seleccionada={convocatoriaSeleccionada?.id === convocatoria.id}
              />
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white rounded-lg border border-dashed border-slate-300 p-10 text-center">
                <AlertCircle className="h-6 w-6 text-slate-400 mx-auto mb-2" />
                <h4 className="font-bold text-slate-700 text-sm">No hay convocatorias con los filtros seleccionados</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Prueba a modificar el término de búsqueda o desactiva el filtro &ldquo;Solo Elegibles&rdquo;.
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

        {vistaActiva === 'pipeline' && (
          <PipelineView
            convocatorias={convocatorias}
            onSeleccionar={(c) => setConvocatoriaSeleccionada(c)}
            onCambiarEstado={handleCambiarEstado}
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
      <footer className="border-t border-slate-200 bg-white py-3 text-center text-xs text-slate-500">
        <p>
          Reforesta · 1hack A Coruña (Common Seeds)
        </p>
      </footer>

    </div>
  );
}
