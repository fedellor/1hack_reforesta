'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { actualizarEstadoBackend, fetchConvocatorias, fetchEmbudo, EmbudoReal } from '@/services/api';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { Header, Seccion, EstadoDatos } from '@/components/Header';
import { Hero, Embudo } from '@/components/Hero';
import { EmpresasView } from '@/components/EmpresasView';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaRowCard } from '@/components/ConvocatoriaRowCard';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { PipelineView } from '@/components/PipelineView';
import { MapView } from '@/components/MapView';
import { CalendarView } from '@/components/CalendarView';
import { AlertCircle } from 'lucide-react';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string; migas: string }> = {
  mapa: { titulo: 'Dónde está la financiación', migas: 'Reforesta / Mapa' },
  convocatorias: { titulo: 'Convocatorias abiertas', migas: 'Reforesta / Convocatorias' },
  calendario: { titulo: 'Calendario de cierres', migas: 'Reforesta / Calendario' },
  empresas: { titulo: 'Empresas y fundaciones que financian', migas: 'Reforesta / Empresas' },
  pipeline: { titulo: 'Pipeline de solicitudes', migas: 'Reforesta / Pipeline' },
};

export default function Home() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [datos, setDatos] = useState<EstadoDatos>({ fuente: 'cargando', actualizado: null });
  const [embudo, setEmbudo] = useState<EmbudoReal | null>(null);
  // Carga desde el backend real y se refresca cada minuto (y al volver a la pestaña)
  const cargar = useCallback(async () => {
    const [r, e] = await Promise.all([fetchConvocatorias(), fetchEmbudo()]);
    // Con datos de ejemplo no se pisan los cambios locales del pipeline
    setConvocatorias((prev) => (r.fuente === 'backend' || prev.length === 0 ? r.convocatorias : prev));
    setEmbudo(e);
    setDatos({ fuente: r.fuente, actualizado: new Date(r.timestamp) });
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargar();
    const intervalo = setInterval(cargar, 60_000);
    const alVolver = () => document.visibilityState === 'visible' && cargar();
    document.addEventListener('visibilitychange', alVolver);
    return () => {
      clearInterval(intervalo);
      document.removeEventListener('visibilitychange', alVolver);
    };
  }, [cargar]);

  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [seccion, setSeccion] = useState<Seccion>('mapa');
  
  const [ordenarPor, setOrdenarPor] = useState<'matching' | 'cuantia' | 'urgencia'>('matching');
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    provincia: '',
    tipoFuente: 'todos',
    soloElegibles: true, // Por defecto ocultamos exclusiones para ahorrar tiempo
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
    ventanaDias: 30, // la plataforma trabaja con un horizonte de 30 días
  });

  // Manejador para actualizar el estado interno en el pipeline
  const handleCambiarEstado = (id: string, nuevoEstado: EstadoInterno) => {
    if (datos.fuente === 'backend') actualizarEstadoBackend(id, nuevoEstado);
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

        // Ventana temporal, encaje, urgencia y cuantía (no aplican al canal de empresas)
        if (seccion === 'empresas') return true;
        if (seccion !== 'calendario' && filtros.ventanaDias > 0 && c.diasRestantes > filtros.ventanaDias) return false;
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
    () => filtrarPorTerritorio(baseFiltrada, filtros.ambito, filtros.provincia),
    [baseFiltrada, filtros.ambito, filtros.provincia]
  );

  const abrir = (c: Convocatoria) => setConvocatoriaSeleccionada(c);
  const conFiltros = seccion !== 'pipeline' && seccion !== 'empresas';

  return (
    <div className="min-h-screen bg-background text-zinc-800 flex flex-col font-sans antialiased">
      <Header
        convocatorias={convocatorias}
        seccion={seccion}
        setSeccion={setSeccion}
        datos={datos}
        onRefresh={cargar}
      />

      <Hero titulo={BANNER[seccion].titulo} migas={BANNER[seccion].migas} />
      {seccion === 'mapa' && <Embudo convocatorias={convocatorias} embudo={embudo} />}

      {conFiltros && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
          ordenarPor={ordenarPor}
          setOrdenarPor={setOrdenarPor}
          modo={seccion === 'convocatorias' ? 'lista' : seccion === 'calendario' ? 'calendario' : 'mapa'}
        />
      )}

      <main className="flex-1 max-w-[1300px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        {seccion === 'mapa' && (
          <MapView
            convocatorias={baseFiltrada}
            filtradas={convocatoriasFiltradas}
            territorio={filtros.ambito}
            provincia={filtros.provincia}
            onCambiarTerritorio={(t) => setFiltros((p) => ({ ...p, ambito: t, provincia: '' }))}
            onCambiarProvincia={(pv) => setFiltros((p) => ({ ...p, provincia: pv }))}
            onSeleccionar={abrir}
            onVerConvocatorias={() => setSeccion('convocatorias')}
          />
        )}

        {seccion === 'convocatorias' && (
          <>
            <p className="text-sm text-zinc-500">
              <strong className="text-zinc-900">{convocatoriasFiltradas.length}</strong> de {convocatorias.length} convocatorias
              {filtros.ambito !== TODOS && (
                <>
                  {' · '}
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS, provincia: '' }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito}{filtros.provincia && ` › ${filtros.provincia}`} ✕
                  </button>
                </>
              )}
            </p>
            <div className="space-y-4">
              {convocatoriasFiltradas.map((convocatoria) => (
                <ConvocatoriaRowCard
                  key={convocatoria.id}
                  convocatoria={convocatoria}
                  onSeleccionar={abrir}
                  seleccionada={convocatoriaSeleccionada?.id === convocatoria.id}
                />
              ))}
              {convocatoriasFiltradas.length === 0 && (
                <div className="border border-dashed border-zinc-300 p-10 text-center">
                  <AlertCircle className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
                  <h4 className="font-bold text-zinc-700">No hay convocatorias con los filtros seleccionados</h4>
                  <p className="text-sm text-zinc-500 mt-1">
                    Amplía la ventana de 30 días, baja el encaje mínimo o desactiva &ldquo;Solo aptas&rdquo;.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {seccion === 'calendario' && <CalendarView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
        {seccion === 'empresas' && <EmpresasView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
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
        <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-8 grid gap-6 sm:grid-cols-3 text-xs">
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
        <div className="bg-black text-center text-xs text-zinc-400 py-2.5 uppercase tracking-wide">
          Declarada de utilidad pública · Prototipo 1hack A Coruña (Common Seeds)
        </div>
      </footer>
    </div>
  );
}
