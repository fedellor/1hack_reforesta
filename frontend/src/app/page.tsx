'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { actualizarEstadoBackend, fetchConvocatorias, fetchEmbudo, fetchHistorico, EmbudoReal } from '@/services/api';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { Header, Seccion, EstadoDatos } from '@/components/Header';
import { Hero, Embudo } from '@/components/Hero';
import { EmpresasView } from '@/components/EmpresasView';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { PipelineView } from '@/components/PipelineView';
import { MapView } from '@/components/MapView';
import { PlanView } from '@/components/PlanView';
import { HistoricoView } from '@/components/HistoricoView';
import { detectarProgramas } from '@/lib/recurrencia';
import { guardarVistas, leerVistas } from '@/lib/novedades';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string; migas: string }> = {
  mapa: { titulo: 'Dónde está la financiación', migas: 'Reforesta / Mapa' },
  plan: { titulo: 'Plan de ataque', migas: 'Reforesta / Plan de ataque' },
  historico: { titulo: 'Histórico y previsión', migas: 'Reforesta / Histórico' },
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
    // Si el backend no responde se conserva lo último cargado (no se vacía la pantalla por un corte puntual)
    setConvocatorias((prev) => (r.fuente === 'backend' ? r.convocatorias : prev));
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

  // Histórico (2020 en adelante): se pide al backend solo al entrar en Histórico o Empresas
  const [historico, setHistorico] = useState<Convocatoria[]>([]);
  const [historicoOk, setHistoricoOk] = useState<boolean | null>(null);
  const [soloNuevas, setSoloNuevas] = useState(false);
  const [vistasDesde, setVistasDesde] = useState<string | null>(null);
  const [idsNuevas, setIdsNuevas] = useState<Set<string>>(new Set());
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [seccion, setSeccion] = useState<Seccion>('mapa');
  
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

        if (soloNuevas && !idsNuevas.has(c.id)) return false;

        // Sección Empresas = solo mecenazgo privado (RSC)
        if (seccion === 'empresas' && c.tipoFuente !== 'privada_rsc') return false;

        // Filtro de elegibilidad (dealbreakers)
        if (filtros.soloElegibles && !c.elegible) {
          return false;
        }

        // Ventana temporal, encaje, urgencia y cuantía (no aplican al canal de empresas)
        if (seccion === 'empresas') return true;
        
        if (c.matchingGlobal < filtros.minMatching) return false;
        if (filtros.soloUrgentes && c.diasRestantes > 15) return false;
        if (c.cuantiaMaximaProyecto < filtros.minCuantia) return false;

        return true;
      })
      .sort((a, b) => b.matchingGlobal - a.matchingGlobal);
  }, [convocatorias, filtros, seccion, soloNuevas, idsNuevas]);

  const convocatoriasFiltradas = useMemo(
    () => filtrarPorTerritorio(baseFiltrada, filtros.ambito, filtros.provincia),
    [baseFiltrada, filtros.ambito, filtros.provincia]
  );

  const programas = useMemo(() => (historico.length ? detectarProgramas(historico) : []), [historico]);

  // Novedades desde la última visita (solo con datos reales; la primera vez se registra todo sin avisar)
  useEffect(() => {
    if (datos.fuente !== 'backend' || convocatorias.length === 0) return;
    const previas = leerVistas();
    if (!previas) {
      guardarVistas(convocatorias.map((c) => c.id));
      return;
    }
    const conocidas = new Set(previas.ids);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIdsNuevas(new Set(convocatorias.filter((c) => !conocidas.has(c.id)).map((c) => c.id)));
    setVistasDesde(previas.desde);
  }, [datos.fuente, convocatorias]);

  const marcarVistas = () => {
    guardarVistas(convocatorias.map((c) => c.id));
    setIdsNuevas(new Set());
    setSoloNuevas(false);
  };

  useEffect(() => {
    if ((seccion === 'historico' || seccion === 'empresas') && historicoOk === null) {
      fetchHistorico().then((r) => {
        setHistorico(r.convocatorias);
        setHistoricoOk(r.disponible);
      });
    }
  }, [seccion, historicoOk]);

  const abrir = (c: Convocatoria) => setConvocatoriaSeleccionada(c);
  const conFiltros = seccion !== 'pipeline' && seccion !== 'empresas' && seccion !== 'historico';

  return (
    <div className="min-h-screen bg-background text-zinc-800 flex flex-col font-sans antialiased">
      <Header
        convocatorias={convocatorias}
        seccion={seccion}
        setSeccion={setSeccion}
        datos={datos}
        onRefresh={cargar}
        nuevas={idsNuevas.size}
        proximaSync={embudo?.proximaSincronizacion ?? null}
      />

      <Hero titulo={BANNER[seccion].titulo} migas={BANNER[seccion].migas} />
      {seccion === 'mapa' && <Embudo convocatorias={convocatorias} embudo={embudo} />}

      {conFiltros && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
        />
      )}

      <main className="flex-1 max-w-[1300px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
        {datos.fuente === 'sin_conexion' && (
          <div className="border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            <strong>Sin conexión con el radar.</strong> No hay datos de respaldo: las convocatorias aparecerán en cuanto el backend esté disponible
            {convocatorias.length > 0 ? ' (se muestra lo último cargado).' : '.'}
          </div>
        )}
        {idsNuevas.size > 0 && (seccion === 'mapa' || seccion === 'plan') && (
          <div className="flex flex-wrap items-center justify-between gap-3 border border-brand/40 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-900">
            <span>
              <strong>{idsNuevas.size}</strong> {idsNuevas.size === 1 ? 'convocatoria nueva' : 'convocatorias nuevas'} desde tu última visita
              {vistasDesde && ` (${new Date(vistasDesde).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })})`}
            </span>
            <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
              <button onClick={() => { setSoloNuevas(!soloNuevas); setSeccion('plan'); }} className="px-3 py-1.5 bg-white border border-brand/40 hover:bg-brand hover:text-white transition-colors">
                {soloNuevas ? 'Ver todas' : 'Ver solo nuevas'}
              </button>
              <button onClick={marcarVistas} className="px-3 py-1.5 text-emerald-800 hover:underline">Marcar como vistas</button>
            </span>
          </div>
        )}
        {seccion === 'mapa' && (
          <MapView
            convocatorias={baseFiltrada}
            filtradas={convocatoriasFiltradas}
            territorio={filtros.ambito}
            provincia={filtros.provincia}
            onCambiarTerritorio={(t) => setFiltros((p) => ({ ...p, ambito: t, provincia: '' }))}
            onCambiarProvincia={(pv) => setFiltros((p) => ({ ...p, provincia: pv }))}
            onSeleccionar={abrir}
            onVerConvocatorias={() => setSeccion('plan')}
          />
        )}

        {seccion === 'plan' && (
          <>
            {(filtros.ambito !== TODOS || soloNuevas) && (
              <p className="text-sm text-zinc-500 flex flex-wrap items-center gap-3">
                {filtros.ambito !== TODOS && (
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS, provincia: '' }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito}{filtros.provincia && ` › ${filtros.provincia}`} ✕
                  </button>
                )}
                {soloNuevas && (
                  <button onClick={() => setSoloNuevas(false)} className="underline hover:text-zinc-900">Solo nuevas ✕</button>
                )}
              </p>
            )}
            <PlanView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />
          </>
        )}
        {seccion === 'historico' && <HistoricoView historico={historico} disponible={historicoOk} onSeleccionar={abrir} />}
        {seccion === 'empresas' && <EmpresasView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} programas={programas} />}
        {seccion === 'pipeline' && (
          <PipelineView convocatorias={convocatorias} onSeleccionar={abrir} onCambiarEstado={handleCambiarEstado} />
        )}
      </main>

      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
        onCambiarEstado={handleCambiarEstado}
      />

      <footer className="bg-[#141414] text-zinc-400 mt-8">
        <div className="max-w-[1300px] mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs flex flex-wrap items-center justify-between gap-2">
          <span>Radar de financiación · uso interno de Reforesta</span>
          <span>Fuentes: BDNS · BOE · boletines autonómicos · fundaciones y programas de empresas</span>
        </div>
      </footer>
    </div>
  );
}
