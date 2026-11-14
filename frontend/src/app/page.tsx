'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  actualizarEstadoBackend,
  fetchConvocatorias,
  fetchEmbudo,
  fetchHistorico,
  fetchReforestaProfile,
  EmbudoReal,
  ReforestaProfile,
} from '@/services/api';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
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
import { guardarVistas, leerVistas } from '@/lib/novedades';
import { puntajeBusqueda } from '@/lib/search';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string; migas: string }> = {
  mapa: { titulo: 'Dónde está la financiación forestal en España', migas: 'Uso Interno / Mapa' },
  plan: { titulo: 'Plan de ataque y plazos', migas: 'Uso Interno / Plan de ataque' },
  prevision: { titulo: 'Previsión de aperturas', migas: 'Uso Interno / Previsión' },
  historico: { titulo: 'Histórico de convocatorias (desde 2016)', migas: 'Uso Interno / Histórico' },
  empresas: { titulo: 'Empresas y fundaciones que financian', migas: 'Uso Interno / Empresas RSC' },
};

export default function Home() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [datos, setDatos] = useState<EstadoDatos>({ fuente: 'cargando', actualizado: null });
  const [embudo, setEmbudo] = useState<EmbudoReal | null>(null);
  const [perfil, setPerfil] = useState<ReforestaProfile | null>(null);
  // Carga desde el backend real y se refresca cada minuto (y al volver a la pestaña)
  const cargar = useCallback(async () => {
    const [r, e, p] = await Promise.all([
      fetchConvocatorias(),
      fetchEmbudo(),
      fetchReforestaProfile(),
    ]);
    // Si el backend no responde se conserva lo último cargado (no se vacía la pantalla por un corte puntual)
    setConvocatorias((prev) => (r.fuente === 'backend' ? r.convocatorias : prev));
    if (e) setEmbudo(e);
    if (p) setPerfil(p);
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
  const [soloNuevas, setSoloNuevas] = useState(false);
  const [verDescartadas, setVerDescartadas] = useState(false);
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
    anio: 0,
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
    const hayBusqueda = Boolean(filtros.busqueda.trim());
    const puntajes = new Map<string, number>();

    const lista = convocatorias.filter((c) => {
      // Búsqueda textual inteligente (sin acentos, sinónimos, MITECO/BDNS/territorio)
      if (hayBusqueda) {
        const pt = puntajeBusqueda(c, filtros.busqueda);
        if (pt <= 0) return false;
        puntajes.set(c.id, pt);
      }

      if (soloNuevas && !idsNuevas.has(c.id)) return false;
      if (c.estadoInterno === 'descartada' && !verDescartadas && seccion !== 'empresas') return false;

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
    });

    return lista.sort((a, b) => {
      if (hayBusqueda) {
        const rel = (puntajes.get(b.id) ?? 0) - (puntajes.get(a.id) ?? 0);
        if (rel !== 0) return rel;
      }
      return b.matchingGlobal - a.matchingGlobal;
    });
  }, [convocatorias, filtros, seccion, soloNuevas, idsNuevas, verDescartadas]);

  const empresasCerradas = useMemo(() => {
    return historico
      .filter((c) => c.estado === 'CERRADA' && c.tipoFuente === 'privada_rsc')
      .filter((c) => !filtros.soloElegibles || c.elegible)
      .filter((c) => !filtros.busqueda.trim() || puntajeBusqueda(c, filtros.busqueda) > 0);
  }, [historico, filtros.soloElegibles, filtros.busqueda]);

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
      <Header
        convocatorias={convocatorias}
        seccion={seccion}
        setSeccion={setSeccion}
        datos={datos}
        onRefresh={cargar}
        nuevas={idsNuevas.size}
        proximaSync={embudo?.proximaSincronizacion ?? null}
        estatutosPdfUrl={perfil?.documentos.estatutos_pdf}
      />

      <Hero titulo={BANNER[seccion].titulo} migas={BANNER[seccion].migas} />
      {seccion === 'mapa' && <Embudo convocatorias={convocatorias} embudo={embudo} />}

      {conFiltros && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
          totalResultados={convocatoriasFiltradas.length}
          onResetFiltros={() =>
            setFiltros({
              busqueda: '',
              ambito: TODOS,
              provincia: '',
              tipoFuente: 'todos',
              soloElegibles: true,
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
            busqueda={filtros.busqueda}
            onLimpiarBusqueda={() => setFiltros((p) => ({ ...p, busqueda: '' }))}
          />
        )}

        {seccion === 'plan' && (
          <>
            {(filtros.ambito !== TODOS || soloNuevas || descartadas > 0) && (
              <p className="text-sm text-zinc-500 flex flex-wrap items-center gap-3">
                {filtros.ambito !== TODOS && (
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS, provincia: '' }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito}{filtros.provincia && ` › ${filtros.provincia}`} ✕
                  </button>
                )}
                {soloNuevas && (
                  <button onClick={() => setSoloNuevas(false)} className="underline hover:text-zinc-900">Solo nuevas ✕</button>
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
            soloElegibles={filtros.soloElegibles}
            onToggleSoloElegibles={() => setFiltros((p) => ({ ...p, soloElegibles: !p.soloElegibles }))}
          />
        )}
      </main>

      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
        onCambiarEstado={handleCambiarEstado}
      />

      <footer className="bg-[#191919] text-[#b8b8b8] mt-10 border-t border-white/10 py-3 px-4 sm:px-6 lg:px-8 text-xs">
        <div className="max-w-[1300px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/reforesta/logo-reforesta-blanco-pie.png"
              alt="Reforesta"
              className="h-5 w-auto object-contain opacity-90"
            />
            <span>Uso interno · Radar de financiación forestal (BDNS · BOE · CCAA · PLACSP · SEDIA · 07:00h)</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-zinc-400">
            <a
              href={
                perfil?.documentos.estatutos_pdf ??
                'https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf'
              }
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#7cc142] transition-colors"
            >
              Estatutos (PDF)
            </a>
            <span>·</span>
            <a
              href={
                perfil?.documentos.utilidad_publica_pdf ??
                'https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf'
              }
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#7cc142] transition-colors"
            >
              Utilidad Pública (PDF)
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
