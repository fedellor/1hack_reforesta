'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  fetchConvocatorias,
  fetchEmbudo,
  fetchHistorico,
  EmbudoReal,
} from '@/services/api';
import { Convocatoria, FiltrosState } from '@/types/convocatoria';
import { Header, Seccion, EstadoDatos } from '@/components/Header';
import { Hero, Embudo } from '@/components/Hero';
import { EmpresasView } from '@/components/EmpresasView';
import { FilterBar } from '@/components/FilterBar';
import { ConvocatoriaDrawer } from '@/components/ConvocatoriaDrawer';
import { MapView } from '@/components/MapView';
import { PlanView } from '@/components/PlanView';
import { HistoricoView } from '@/components/HistoricoView';
import { PrevisionView } from '@/components/PrevisionView';
import { detectarProgramas } from '@/lib/recurrencia';
import { puntajeBusqueda } from '@/lib/search';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string }> = {
  mapa: { titulo: 'Dónde está la financiación forestal en España' },
  plan: { titulo: 'Plan de ataque y plazos' },
  prevision: { titulo: 'Previsión de aperturas' },
  historico: { titulo: 'Histórico de convocatorias (desde 2016)' },
  empresas: { titulo: 'Empresas y fundaciones que financian' },
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
    if (e) setEmbudo(e);
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

  // Histórico (2016 en adelante): se pide al backend al entrar en Histórico, Previsión o Empresas
  const [historico, setHistorico] = useState<Convocatoria[]>([]);
  const [historicoOk, setHistoricoOk] = useState<boolean | null>(null);
  const [verDescartadas, setVerDescartadas] = useState(false);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [seccion, setSeccion] = useState<Seccion>('mapa');
  
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    provincia: '',
    tipoFuente: 'todos',
    elegibilidad: 'aptas',
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
    ventanaDias: 30, // la plataforma trabaja con un horizonte de 30 días
    anio: 0,
  });

  // Filtrado común previo a elegibilidad y territorio (alimenta conteos coherentes)
  const sinElegibilidad = useMemo(() => {
    const hayBusqueda = Boolean(filtros.busqueda.trim());
    const puntajes = new Map<string, number>();

    const lista = convocatorias.filter((c) => {
      // Búsqueda textual inteligente (sin acentos, sinónimos, MITECO/BDNS/territorio)
      if (hayBusqueda) {
        const pt = puntajeBusqueda(c, filtros.busqueda);
        if (pt <= 0) return false;
        puntajes.set(c.id, pt);
      }

      if (c.estadoInterno === 'descartada' && !verDescartadas && seccion !== 'empresas') return false;

      // Sección Empresas = solo mecenazgo privado (RSC)
      if (seccion === 'empresas' && c.tipoFuente !== 'privada_rsc') return false;

      // Ventana temporal, encaje, urgencia y cuantía (no aplican al canal de empresas)
      if (seccion === 'empresas') return true;

      if (c.matchingGlobal < filtros.minMatching) return false;
      if (filtros.soloUrgentes && c.diasRestantes > 15) return false;

      return true;
    });

    return lista.sort((a, b) => {
      if (hayBusqueda) {
        const rel = (puntajes.get(b.id) ?? 0) - (puntajes.get(a.id) ?? 0);
        if (rel !== 0) return rel;
      }
      return b.matchingGlobal - a.matchingGlobal;
    });
  }, [convocatorias, filtros.busqueda, filtros.minMatching, filtros.soloUrgentes, seccion, verDescartadas]);

  // Filtros comunes SIN territorio (el mapa se colorea con esta lista)
  const baseFiltrada = useMemo(() => {
    return sinElegibilidad.filter((c) =>
      filtros.elegibilidad === 'aptas' ? c.elegible : !c.elegible
    );
  }, [sinElegibilidad, filtros.elegibilidad]);

  const conteoElegibilidad = useMemo(() => {
    const enTerritorio = filtrarPorTerritorio(sinElegibilidad, filtros.ambito, filtros.provincia);
    const aptas = enTerritorio.filter((c) => c.elegible).length;
    return { aptas, excluidas: enTerritorio.length - aptas };
  }, [sinElegibilidad, filtros.ambito, filtros.provincia]);

  const empresasCerradas = useMemo(() => {
    return historico
      .filter((c) => c.estado === 'CERRADA' && c.tipoFuente === 'privada_rsc')
      .filter((c) => (filtros.elegibilidad === 'aptas' ? c.elegible : !c.elegible))
      .filter((c) => !filtros.busqueda.trim() || puntajeBusqueda(c, filtros.busqueda) > 0);
  }, [historico, filtros.elegibilidad, filtros.busqueda]);

  const convocatoriasFiltradas = useMemo(
    () => filtrarPorTerritorio(baseFiltrada, filtros.ambito, filtros.provincia),
    [baseFiltrada, filtros.ambito, filtros.provincia]
  );

  const programas = useMemo(() => (historico.length ? detectarProgramas(historico) : []), [historico]);

  useEffect(() => {
    if ((seccion === 'historico' || seccion === 'prevision' || seccion === 'empresas') && historicoOk === null) {
      fetchHistorico().then((r) => {
        setHistorico(r.convocatorias);
        setHistoricoOk(r.disponible);
      });
    }
  }, [seccion, historicoOk]);

  const abrir = (c: Convocatoria) => setConvocatoriaSeleccionada(c);
  const conFiltros = seccion === 'mapa' || seccion === 'plan';
  const descartadas = convocatorias.filter((c) => c.estadoInterno === 'descartada').length;

  return (
    <div className="min-h-screen bg-background text-zinc-800 flex flex-col font-sans antialiased">
      <Header seccion={seccion} setSeccion={setSeccion} />

      <Hero titulo={BANNER[seccion].titulo} />
      {seccion === 'mapa' && <Embudo convocatorias={convocatorias} embudo={embudo} />}

      {conFiltros && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
          totalResultados={convocatoriasFiltradas.length}
          conteoElegibilidad={conteoElegibilidad}
          onResetFiltros={() =>
            setFiltros({
              busqueda: '',
              ambito: TODOS,
              provincia: '',
              tipoFuente: 'todos',
              elegibilidad: 'aptas',
              minMatching: 0,
              soloUrgentes: false,
              minCuantia: 0,
              ventanaDias: 30,
              anio: 0,
            })
          }
        />
      )}

      <main className="flex-1 max-w-[1300px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {datos.fuente === 'sin_conexion' && (
          <div className="border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            <strong>Sin conexión con el radar.</strong> No hay datos de respaldo: las convocatorias aparecerán en cuanto el backend esté disponible
            {convocatorias.length > 0 ? ' (se muestra lo último cargado).' : '.'}
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
            busqueda={filtros.busqueda}
            onLimpiarBusqueda={() => setFiltros((p) => ({ ...p, busqueda: '' }))}
          />
        )}

        {seccion === 'plan' && (
          <>
            {(filtros.ambito !== TODOS || descartadas > 0) && (
              <p className="text-sm text-zinc-500 flex flex-wrap items-center gap-3">
                {filtros.ambito !== TODOS && (
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS, provincia: '' }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito}{filtros.provincia && ` › ${filtros.provincia}`} ✕
                  </button>
                )}
                {descartadas > 0 && (
                  <button onClick={() => setVerDescartadas(!verDescartadas)} className="underline hover:text-zinc-900">
                    {verDescartadas ? 'Ocultar' : 'Mostrar'} {descartadas} descartadas
                  </button>
                )}
              </p>
            )}
            <PlanView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />
          </>
        )}
        {seccion === 'prevision' && <PrevisionView historico={historico} disponible={historicoOk} onSeleccionar={abrir} />}
        {seccion === 'historico' && <HistoricoView historico={historico} disponible={historicoOk} onSeleccionar={abrir} />}
        {seccion === 'empresas' && (
          <EmpresasView
            convocatorias={convocatoriasFiltradas}
            cerradas={empresasCerradas}
            onSeleccionar={abrir}
            programas={programas}
            elegibilidad={filtros.elegibilidad}
            onCambiarElegibilidad={(elegibilidad) => setFiltros((p) => ({ ...p, elegibilidad }))}
          />
        )}
      </main>

      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
      />

    </div>
  );
}
