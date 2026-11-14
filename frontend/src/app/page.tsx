'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';
import { Convocatoria, FiltrosState, EstadoInterno } from '@/types/convocatoria';
import { fetchConvocatorias } from '@/services/api';
import { Header, Seccion } from '@/components/Header';
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
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>(MOCK_CONVOCATORIAS);
  const [convocatoriaSeleccionada, setConvocatoriaSeleccionada] = useState<Convocatoria | null>(null);
  const [seccion, setSeccion] = useState<Seccion>('mapa');
  
  const [ordenarPor, setOrdenarPor] = useState<'matching' | 'cuantia' | 'urgencia'>('matching');
  const [filtros, setFiltros] = useState<FiltrosState>({
    busqueda: '',
    ambito: 'todos',
    tipoFuente: 'todos',
    soloElegibles: true, // Por defecto ocultamos exclusiones para ahorrar tiempo
    minMatching: 0,
    soloUrgentes: false,
    minCuantia: 0,
    ventanaDias: 0, // Mostrar todas las convocatorias reales activas en España por defecto (filtrable a ≤ 30 días)
  });

  // Manejador para actualizar el estado interno en el pipeline (y persistirlo en el backend de Diego)
  const cargarDesdeBackend = useCallback(async () => {
    const resp = await fetchConvocatorias();
    if (resp.convocatorias && resp.convocatorias.length > 0) {
      setConvocatorias(resp.convocatorias);
    }
  }, []);

  useEffect(() => {
    cargarDesdeBackend();
  }, [cargarDesdeBackend]);

  const handleCambiarEstado = (id: string, nuevoEstado: EstadoInterno) => {
    setConvocatorias((prev) =>
      prev.map((c) => (c.id === id ? { ...c, estadoInterno: nuevoEstado } : c))
    );
    if (convocatoriaSeleccionada && convocatoriaSeleccionada.id === id) {
      setConvocatoriaSeleccionada((prev) => (prev ? { ...prev, estadoInterno: nuevoEstado } : null));
    }
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/convocatorias/${encodeURIComponent(id)}/estado`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estadoInterno: nuevoEstado }),
    }).catch(() => {});
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
  const conFiltros = seccion !== 'pipeline' && seccion !== 'empresas';

  return (
    <div className="min-h-screen bg-background text-zinc-800 flex flex-col font-sans antialiased">
      <Header
        convocatorias={convocatorias}
        seccion={seccion}
        setSeccion={setSeccion}
        onRefresh={async () => {
          await cargarDesdeBackend();
        }}
      />

      <Hero titulo={BANNER[seccion].titulo} migas={BANNER[seccion].migas} />
      {seccion === 'mapa' && <Embudo convocatorias={convocatorias} />}

      {conFiltros && (
        <FilterBar filtros={filtros} setFiltros={setFiltros} ordenarPor={ordenarPor} setOrdenarPor={setOrdenarPor} />
      )}

      <main className="flex-1 max-w-[1300px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        {seccion === 'mapa' && (
          <MapView
            convocatorias={baseFiltrada}
            filtradas={convocatoriasFiltradas}
            territorio={filtros.ambito}
            onCambiarTerritorio={(t) => setFiltros((p) => ({ ...p, ambito: t }))}
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
                  <button onClick={() => setFiltros((p) => ({ ...p, ambito: TODOS }))} className="underline hover:text-zinc-900">
                    {filtros.ambito === ESTATAL ? 'Ámbito estatal' : filtros.ambito} ✕
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

      {/* Footer corporativo idéntico a https://reforesta.es/ (#Footer) */}
      <footer className="bg-[#191919] text-[#cccccc] mt-12 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid gap-8 md:grid-cols-4 text-sm">
          {/* Columna 1: Logo blanco oficial de Reforesta */}
          <div className="flex flex-col items-start">
            <a href="https://reforesta.es/" target="_blank" rel="noopener noreferrer">
              <img
                src="/reforesta/logo-reforesta-blanco-pie.png"
                alt="Reforesta"
                className="w-[155px] h-auto object-contain"
              />
            </a>
            <a
              href="https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block text-[11px] uppercase tracking-wider text-[#7cc142] hover:underline font-semibold"
            >
              Declarada de Utilidad Pública ↗
            </a>
          </div>

          {/* Columna 2: Descripción oficial de reforesta.es */}
          <div>
            <h4 className="text-white font-semibold text-base mb-3">Descripción</h4>
            <p className="text-[13px] leading-relaxed text-[#b8b8b8]">
              ONG creada en 1991 para la conservación de la naturaleza, declarada de Utilidad Pública.
              Jornadas de voluntariado con particulares y empresas. Trabajamos por los bosques.
            </p>
            <p className="mt-3 text-[12px] text-[#999999]">
              Contacto:{' '}
              <a href="mailto:info@reforesta.es" className="text-[#7cc142] hover:underline">
                info@reforesta.es
              </a>
            </p>
          </div>

          {/* Columna 3: Posts recientes y Fuentes Oficiales conectadas */}
          <div>
            <h4 className="text-white font-semibold text-base mb-3">Posts recientes &amp; Fuentes</h4>
            <ul className="space-y-2.5 text-[12px]">
              <li className="border-b border-white/10 pb-2">
                <a
                  href="https://reforesta.es/2026/03/23/21-de-marzo-dia-forestal-mundial/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-[#7cc142] transition-colors font-medium block"
                >
                  21 de marzo, Día Forestal Mundial
                </a>
                <span className="text-[11px] text-zinc-400">23 marzo, 2026 · Reforesta.es</span>
              </li>
              <li className="border-b border-white/10 pb-2">
                <a
                  href="https://reforesta.es/2026/02/03/reforesta-restaura-una-importante-zona-de-recarga-del-acuifero-de-madrid/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-[#7cc142] transition-colors font-medium block"
                >
                  Reforesta restaura una importante zona de recarga del acuífero de Madrid
                </a>
                <span className="text-[11px] text-zinc-400">3 febrero, 2026 · Reforesta.es</span>
              </li>
              <li className="text-[11px] text-zinc-400 pt-0.5">
                Radar conectado a BDNS · BOE · 19 Boletines CCAA · PLACSP · LIFE/SEDIA · Fundaciones RSC
              </li>
            </ul>
          </div>

          {/* Columna 4: Redes sociales circulares verdes (#6aa43a) idénticas a reforesta.es */}
          <div>
            <h4 className="text-white font-semibold text-base mb-3">Síguenos</h4>
            <div className="flex flex-wrap items-center gap-2.5">
              <a
                href="https://www.facebook.com/asociacion.reforesta"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Facebook"
                className="w-10 h-10 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-sm transition-colors"
              >
                f
              </a>
              <a
                href="https://twitter.com/Reforesta_ONG"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="X Twitter"
                className="w-10 h-10 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-sm transition-colors"
              >
                𝕏
              </a>
              <a
                href="https://www.instagram.com/reforesta_ong/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="w-10 h-10 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-xs transition-colors"
              >
                IG
              </a>
              <a
                href="https://www.youtube.com/c/Reforesta_ong"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="YouTube"
                className="w-10 h-10 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-xs transition-colors"
              >
                ▶
              </a>
              <a
                href="https://www.linkedin.com/company/asociacion-reforesta/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                className="w-10 h-10 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-xs transition-colors"
              >
                in
              </a>
            </div>
          </div>
        </div>

        {/* Franja inferior de copyright y enlaces legales de reforesta.es */}
        <div className="bg-[#111111] border-t border-white/10 py-4 px-4 sm:px-6 lg:px-8 text-xs text-zinc-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>Copyright © Reforesta. Todos los derechos reservados.</div>
            <div className="flex items-center gap-2">
              <a
                href="https://reforesta.es/politica-de-privacidad/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#7cc142] transition-colors"
              >
                Política de Privacidad
              </a>
              <span>|</span>
              <a
                href="https://reforesta.es/aviso-legal/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#7cc142] transition-colors"
              >
                Aviso legal
              </a>
              <span>|</span>
              <a
                href="https://reforesta.es/politica-de-cookies/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#7cc142] transition-colors"
              >
                Política de Cookies
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
