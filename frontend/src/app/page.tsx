'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  actualizarEstadoBackend,
  fetchConvocatorias,
  fetchEmbudo,
  fetchReforestaProfile,
  EmbudoReal,
  ReforestaProfile,
} from '@/services/api';
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
import { ESTATAL, TODOS, filtrarPorTerritorio, formatoEuros } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string; migas: string }> = {
  mapa: { titulo: 'Dónde está la financiación forestal en España', migas: 'Uso Interno / Mapa' },
  convocatorias: { titulo: 'Convocatorias activas y próximas', migas: 'Uso Interno / Convocatorias' },
  historico: { titulo: 'Histórico de convocatorias (2020–2026)', migas: 'Uso Interno / Histórico 2020–2026' },
  calendario: { titulo: 'Calendario de cierres y plazos', migas: 'Uso Interno / Calendario' },
  empresas: { titulo: 'Empresas, fundaciones y mecenazgo RSC', migas: 'Uso Interno / Empresas RSC' },
  pipeline: { titulo: 'Pipeline de solicitudes Reforesta', migas: 'Uso Interno / Pipeline' },
};

const ANIOS_HISTORICO = [2026, 2025, 2024, 2023, 2022, 2021, 2020];

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
    setConvocatorias((prev) => (r.fuente === 'backend' || prev.length === 0 ? r.convocatorias : prev));
    if (e) setEmbudo(e);
    if (p) setPerfil(p);
    setDatos({ fuente: r.fuente, actualizado: new Date(r.timestamp) });
  }, []);

  useEffect(() => {
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
    ambito: TODOS,
    provincia: '',
    tipoFuente: 'todos',
    soloElegibles: true,
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
    ventanaDias: 0,
    anio: 0,
  });

  const handleCambiarEstado = (id: string, nuevoEstado: EstadoInterno) => {
    if (datos.fuente === 'backend') {
      actualizarEstadoBackend(id, nuevoEstado);
    }
    setConvocatorias((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estadoInterno: nuevoEstado } : c))
    );
    if (convocatoriaSeleccionada && convocatoriaSeleccionada.id === id) {
      setConvocatoriaSeleccionada((prev) => (prev ? { ...prev, estadoInterno: nuevoEstado } : null));
    }
  };

  const convocatoriasAbiertas = useMemo(
    () => convocatorias.filter((c) => c.estado !== 'CERRADA'),
    [convocatorias]
  );

  const convocatoriasHistoricas = useMemo(
    () => convocatorias.filter((c) => c.estado === 'CERRADA'),
    [convocatorias]
  );

  const conteoPorAnio = useMemo(() => {
    const counts: Record<number, number> = { 2026: 0, 2025: 0, 2024: 0, 2023: 0, 2022: 0, 2021: 0, 2020: 0 };
    for (const c of convocatoriasHistoricas) {
      const y = c.anio ?? Number(String(c.fechaCierre).slice(0, 4));
      if (y in counts) counts[y] += 1;
    }
    return counts;
  }, [convocatoriasHistoricas]);

  // Filtros comunes SIN territorio (el mapa se colorea con esta lista)
  const baseFiltrada = useMemo(() => {
    const pool = seccion === 'historico' ? convocatoriasHistoricas : convocatoriasAbiertas;
    return pool
      .filter((c) => {
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

        if (seccion === 'historico' && filtros.anio > 0) {
          const y = c.anio ?? Number(String(c.fechaCierre).slice(0, 4));
          if (y !== filtros.anio) return false;
        }

        if (seccion === 'empresas' && c.tipoFuente !== 'privada_rsc') return false;
        if (filtros.soloElegibles && !c.elegible) return false;
        if (seccion === 'empresas') return true;
        if (
          seccion !== 'calendario' &&
          seccion !== 'historico' &&
          filtros.ventanaDias > 0 &&
          c.diasRestantes > filtros.ventanaDias
        ) {
          return false;
        }
        if (c.matchingGlobal < filtros.minMatching) return false;
        if (filtros.soloUrgentes && c.diasRestantes > 15) return false;
        if (c.cuantiaMaximaProyecto < filtros.minCuantia) return false;

        return true;
      })
      .sort((a, b) => {
        if (ordenarPor === 'matching') return b.matchingGlobal - a.matchingGlobal;
        if (ordenarPor === 'cuantia') return b.cuantiaMaximaProyecto - a.cuantiaMaximaProyecto;
        if (ordenarPor === 'urgencia') {
          return seccion === 'historico'
            ? b.fechaCierre.localeCompare(a.fechaCierre)
            : a.diasRestantes - b.diasRestantes;
        }
        return 0;
      });
  }, [convocatoriasAbiertas, convocatoriasHistoricas, filtros, ordenarPor, seccion]);

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
      {seccion === 'mapa' && <Embudo convocatorias={convocatoriasAbiertas} embudo={embudo} />}

      {conFiltros && (
        <FilterBar
          filtros={filtros}
          setFiltros={setFiltros}
          ordenarPor={ordenarPor}
          setOrdenarPor={setOrdenarPor}
          modo={
            seccion === 'convocatorias'
              ? 'lista'
              : seccion === 'historico'
                ? 'historico'
                : seccion === 'calendario'
                  ? 'calendario'
                  : 'mapa'
          }
        />
      )}

      <main className="flex-1 max-w-[1300px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
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
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-zinc-500">
              <p>
                <strong className="text-zinc-900">{convocatoriasFiltradas.length}</strong> de{' '}
                {convocatoriasAbiertas.length} convocatorias activas o próximas en España
                {filtros.ambito !== TODOS && (
                  <>
                    {' · '}
                    <button
                      onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS, provincia: '' }))}
                      className="underline hover:text-zinc-900 cursor-pointer"
                    >
                      {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito}
                      {filtros.provincia && ` › ${filtros.provincia}`} ✕
                    </button>
                  </>
                )}
              </p>
              {filtros.soloElegibles && convocatoriasAbiertas.some((c) => !c.elegible) && (
                <button
                  type="button"
                  onClick={() => setFiltros((p) => ({ ...p, soloElegibles: false }))}
                  className="text-xs px-3 py-1 rounded-full border border-zinc-200 bg-white text-zinc-600 hover:border-[#6aa43a] hover:text-[#2d5a27] transition-colors cursor-pointer"
                >
                  +{convocatoriasAbiertas.filter((c) => !c.elegible).length} licitaciones / otras entidades ocultas · Ver todas
                </button>
              )}
            </div>
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
                  <h4 className="font-bold text-zinc-700">No hay convocatorias abiertas con los filtros seleccionados</h4>
                  <p className="text-sm text-zinc-500 mt-1">
                    Amplía la ventana temporal, baja el encaje mínimo o desactiva &ldquo;Solo aptas ONG&rdquo; para incluir licitaciones públicas.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {seccion === 'historico' && (
          <>
            <div className="bg-white border border-zinc-200 rounded-sm p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-600">
                <span>
                  Mostrando <strong className="text-zinc-900">{convocatoriasFiltradas.length}</strong> de{' '}
                  <strong className="text-zinc-900">{convocatoriasHistoricas.length}</strong> convocatorias cerradas
                  (archivo 2020–2026) · Presupuesto filtrado:{' '}
                  <strong className="text-[#2d5a27]">
                    {formatoEuros(convocatoriasFiltradas.reduce((acc, c) => acc + (c.presupuestoTotal ?? 0), 0))}
                  </strong>
                </span>
                {filtros.soloElegibles && convocatoriasHistoricas.some((c) => !c.elegible) && (
                  <button
                    type="button"
                    onClick={() => setFiltros((p) => ({ ...p, soloElegibles: false }))}
                    className="text-xs px-3 py-1 rounded-full border border-zinc-200 bg-zinc-50 text-zinc-600 hover:border-[#6aa43a] hover:text-[#2d5a27] transition-colors cursor-pointer"
                  >
                    Incluir no elegibles ONG ({convocatoriasHistoricas.filter((c) => !c.elegible).length})
                  </button>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setFiltros((p) => ({ ...p, anio: 0 }))}
                  className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors cursor-pointer ${
                    filtros.anio === 0
                      ? 'bg-[#6aa43a] border-[#6aa43a] text-white'
                      : 'bg-zinc-50 border-zinc-200 text-zinc-700 hover:bg-zinc-100'
                  }`}
                >
                  Todos ({convocatoriasHistoricas.length})
                </button>
                {ANIOS_HISTORICO.map((y) => (
                  <button
                    key={y}
                    type="button"
                    onClick={() => setFiltros((p) => ({ ...p, anio: p.anio === y ? 0 : y }))}
                    className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors cursor-pointer ${
                      filtros.anio === y
                        ? 'bg-[#6aa43a] border-[#6aa43a] text-white'
                        : 'bg-zinc-50 border-zinc-200 text-zinc-700 hover:bg-zinc-100'
                    }`}
                  >
                    {y} ({conteoPorAnio[y] ?? 0})
                  </button>
                ))}
              </div>
            </div>

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
                  <h4 className="font-bold text-zinc-700">No hay convocatorias históricas con los filtros actuales</h4>
                  <p className="text-sm text-zinc-500 mt-1">
                    Prueba otro año, limpia el término de búsqueda o desactiva &ldquo;Solo aptas ONG&rdquo;.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {seccion === 'calendario' && <CalendarView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
        {seccion === 'empresas' && <EmpresasView convocatorias={convocatoriasFiltradas} onSeleccionar={abrir} />}
        {seccion === 'pipeline' && (
          <PipelineView
            convocatorias={convocatorias.filter((c) => c.estado !== 'CERRADA' || c.estadoInterno !== 'nueva')}
            onSeleccionar={abrir}
            onCambiarEstado={handleCambiarEstado}
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
