'use client';

import React, { useState, useMemo } from 'react';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { Header, Seccion } from '@/components/Header';
import { Hero } from '@/components/Hero';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaRowCard } from '@/components/ConvocatoriaRowCard';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { TableView } from '@/components/TableView';
import { PipelineView } from '@/components/PipelineView';
import { MapView } from '@/components/MapView';
import { CalendarView } from '@/components/CalendarView';
import { AlertCircle, CalendarDays, List, Map as MapIcon, Table2 } from 'lucide-react';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

type Vista = 'lista' | 'tabla' | 'calendario' | 'mapa';

const VISTAS: { id: Vista; label: string; icono: React.ComponentType<{ className?: string }> }[] = [
  { id: 'lista', label: 'Lista', icono: List },
  { id: 'tabla', label: 'Tabla', icono: Table2 },
  { id: 'calendario', label: 'Calendario', icono: CalendarDays },
  { id: 'mapa', label: 'Mapa', icono: MapIcon },
];

export default function Home() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>(MOCK_CONVOCATORIAS);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [seccion, setSeccion] = useState<Seccion>('radar');
  const [vista, setVista] = useState<Vista>('lista');
  
  const [ordenarPor, setOrdenarPor] = useState<'matching' | 'cuantia' | 'urgencia'>('matching');
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    tipoFuente: 'todos',
    soloElegibles: true, // Por defecto ocultamos exclusiones para ahorrar tiempo
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
    ventanaDias: 30, // la plataforma trabaja con un horizonte de 30 días
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
  // Filtros comunes SIN territorio (el mapa se colorea con esta lista)
  const baseFiltrada = useMemo(() => {
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

        // Sección Empresas = solo mecenazgo privado (RSC)
        if (seccion === 'empresas' && c.tipoFuente !== 'privada_rsc') return false;

        // Filtro de elegibilidad (dealbreakers)
        if (filtros.soloElegibles && !c.elegible) {
          return false;
        }

        // Ventana temporal, encaje, urgencia y cuantía
        if (filtros.ventanaDias > 0 && c.diasRestantes > filtros.ventanaDias) return false;
        if (c.matchingGlobal < filtros.minMatching) return false;
        if (filtros.soloUrgentes && c.diasRestantes > 15) return false;
        if (c.cuantiaMaximaProyecto < filtros.minCuantia) return false;

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
  }, [convocatorias, filtros, ordenarPor, seccion]);

  const convocatoriasFiltradas = useMemo(
    () => filtrarPorTerritorio(baseFiltrada, filtros.ambito),
    [baseFiltrada, filtros.ambito]
  );

  const abrir = (c: Convocatoria) => setConvocatoriaSeleccionada(c);
  const enRadar = seccion !== 'pipeline';

  return (
    <div className="min-h-screen bg-background text-zinc-800 flex flex-col font-sans antialiased">
      <Header
        convocatorias={convocatorias}
        seccion={seccion}
        setSeccion={setSeccion}
        onRefresh={() => {
          alert('Convocatorias sincronizadas con fuentes oficiales (BDNS, BOE y CCAA).');
        }}
      />

      {/* Cabecera de página: una sola por sección */}
      {seccion === 'radar' && <Hero convocatorias={convocatorias} />}
      {seccion === 'empresas' && (
        <section className="bg-[#141414] text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">Canal de mecenazgo</p>
            <h1 className="mt-2 text-2xl sm:text-3xl font-bold">Empresas y fundaciones que financian reforestación</h1>
            <p className="mt-2 max-w-2xl text-sm text-white/70">
              Hoy este canal está a cero: solo atienden a empresas que llaman a su puerta. Objetivo: captar 2–4 empresas.
            </p>
          </div>
        </section>
      )}
      {seccion === 'pipeline' && (
        <section className="bg-[#141414] text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">Seguimiento del equipo</p>
            <h1 className="mt-2 text-2xl sm:text-3xl font-bold">Pipeline de solicitudes</h1>
          </div>
        </section>
      )}

      {/* Filtros: compartidos por todas las vistas */}
      {enRadar && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
          ordenarPor={ordenarPor}
          setOrdenarPor={setOrdenarPor}
        />
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 space-y-4">
        {enRadar && (
          <div className="flex items-center justify-between gap-3 text-xs">
            <p className="text-zinc-500">
              <strong className="text-zinc-900">{convocatoriasFiltradas.length}</strong> de {convocatorias.length} convocatorias
              {filtros.ambito !== TODOS && (
                <>
                  {' · '}
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito} ✕
                  </button>
                </>
              )}
            </p>
            <div className="inline-flex rounded-md border border-zinc-200 bg-white p-0.5">
              {VISTAS.map(({ id, label, icono: Icono }) => (
                <button
                  key={id}
                  onClick={() => setVista(id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded font-medium transition-colors ${
                    vista === id ? 'bg-[#333] text-white' : 'text-zinc-600 hover:text-zinc-900'
                  }`}
                >
                  <Icono className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {enRadar && vista === 'lista' && (
          <div className="space-y-2.5">
            {convocatoriasFiltradas.map((convocatoria) => (
              <ConvocatoriaRowCard
                key={convocatoria.id}
                convocatoria={convocatoria}
                onSeleccionar={abrir}
                seleccionada={convocatoriaSeleccionada?.id === convocatoria.id}
              />
            ))}

            {convocatoriasFiltradas.length === 0 && (
              <div className="bg-white rounded-lg border border-dashed border-zinc-300 p-10 text-center">
                <AlertCircle className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
                <h4 className="font-bold text-zinc-700 text-sm">No hay convocatorias con los filtros seleccionados</h4>
                <p className="text-xs text-zinc-500 mt-1">
                  Amplía la ventana de 30 días, baja el encaje mínimo o desactiva &ldquo;Solo aptas&rdquo;.
                </p>
              </div>
            )}
          </div>
        )}

        {enRadar && vista === 'tabla' && <TableView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
        {enRadar && vista === 'calendario' && <CalendarView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
        {enRadar && vista === 'mapa' && (
          <MapView
            convocatorias={baseFiltrada}
            filtradas={convocatoriasFiltradas}
            territorio={filtros.ambito}
            onCambiarTerritorio={(t) => setFiltros((p) => ({ ...p, ambito: t }))}
            onSeleccionar={abrir}
          />
        )}

        {seccion === 'pipeline' && (
          <PipelineView convocatorias={convocatorias} onSeleccionar={abrir} onCambiarEstado={handleCambiarEstado} />
        )}
      </main>

      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
        onCambiarEstado={handleCambiarEstado}
      />

      {/* Footer institucional */}
      <footer className="bg-[#141414] text-zinc-300 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid gap-6 sm:grid-cols-3 text-xs">
          <div>
            <p className="font-serif tracking-[0.2em] text-sm font-bold text-brand">REFORESTA</p>
            <p className="mt-2 leading-relaxed text-zinc-400">
              ONG creada en 1991 para la conservación de la naturaleza, declarada de Utilidad Pública.
            </p>
          </div>
          <div>
            <p className="font-serif font-bold text-white">Contacto</p>
            <p className="mt-2 text-zinc-400">info@reforesta.es</p>
            <p className="text-zinc-400">Tres Cantos (Madrid)</p>
          </div>
          <div>
            <p className="font-serif font-bold text-white">Fuentes</p>
            <p className="mt-2 text-zinc-400">BDNS · BOE · Boletines autonómicos · Fundaciones y programas RSC</p>
          </div>
        </div>
        <div className="bg-black text-center text-[11px] text-zinc-400 py-2.5 uppercase tracking-wide">
          Declarada de utilidad pública · Prototipo 1hack A Coruña (Common Seeds)
        </div>
      </footer>
    </div>
  );
}
