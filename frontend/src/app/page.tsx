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
import { AlertCircle, ShieldCheck, FileText, Building2 } from 'lucide-react';
import { ESTATAL, TODOS, filtrarPorTerritorio } from '@/lib/territorio';

const BANNER: Record<Seccion, { titulo: string; migas: string }> = {
  mapa: { titulo: 'Dónde está la financiación forestal en España', migas: 'Reforesta / Mapa' },
  convocatorias: { titulo: 'Convocatorias reales de reforestación', migas: 'Reforesta / Convocatorias' },
  calendario: { titulo: 'Calendario de cierres y plazos', migas: 'Reforesta / Calendario' },
  empresas: { titulo: 'Empresas, fundaciones y mecenazgo RSC', migas: 'Reforesta / Empresas RSC' },
  pipeline: { titulo: 'Pipeline de solicitudes Reforesta', migas: 'Reforesta / Pipeline' },
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

  // Filtros comunes SIN territorio (el mapa se colorea con esta lista)
  const baseFiltrada = useMemo(() => {
    return convocatorias
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

        if (seccion === 'empresas' && c.tipoFuente !== 'privada_rsc') return false;
        if (filtros.soloElegibles && !c.elegible) return false;
        if (seccion === 'empresas') return true;
        if (seccion !== 'calendario' && filtros.ventanaDias > 0 && c.diasRestantes > filtros.ventanaDias) return false;
        if (c.matchingGlobal < filtros.minMatching) return false;
        if (filtros.soloUrgentes && c.diasRestantes > 15) return false;
        if (c.cuantiaMaximaProyecto < filtros.minCuantia) return false;

        return true;
      })
      .sort((a, b) => {
        if (ordenarPor === 'matching') return b.matchingGlobal - a.matchingGlobal;
        if (ordenarPor === 'cuantia') return b.cuantiaMaximaProyecto - a.cuantiaMaximaProyecto;
        if (ordenarPor === 'urgencia') return a.diasRestantes - b.diasRestantes;
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
            <p className="text-sm text-zinc-500">
              <strong className="text-zinc-900">{convocatoriasFiltradas.length}</strong> de {convocatorias.length}{' '}
              convocatorias reales en España
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
                    Amplía la ventana temporal, baja el encaje mínimo o desactiva &ldquo;Solo aptas&rdquo;.
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

        {/* Tarjeta institucional compacta: Perfil Estatutario Oficial de Asociación Reforesta */}
        <section className="border border-[#6aa43a]/30 bg-[#f6faf2] rounded-sm p-5 mt-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[#2d5a27] text-xs font-bold uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-[#6aa43a]" />
                <span>Perfil Estatutario Verificado · {perfil?.nombre ?? 'ASOCIACIÓN REFORESTA'}</span>
              </div>
              <p className="text-xs text-zinc-700 leading-relaxed">
                <strong>NIF {perfil?.nif ?? 'G80428204'}</strong> · Registro Nacional de Asociaciones{' '}
                {perfil?.registro_nacional ?? 'Grupo 1, Sección 1, Nº 162965'} · Fundada en{' '}
                {perfil?.anio_fundacion ?? 1991} ·{' '}
                {perfil?.domicilio_social ?? 'Sector Foresta 43, Oficina 33, 28760 Tres Cantos (Madrid)'}.
                El algoritmo evalúa automáticamente los <strong>11 fines estatutarios</strong> (conservación, lucha
                contra la desertificación, educación ambiental, empleo verde e inclusión) y las deducciones fiscales de
                <strong> Utilidad Pública</strong>.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <a
                href={
                  perfil?.documentos.estatutos_pdf ??
                  'https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf'
                }
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-zinc-300 text-zinc-800 hover:border-[#6aa43a] hover:text-[#2d5a27] rounded-sm transition-colors"
              >
                <FileText className="w-3.5 h-3.5 text-[#6aa43a]" />
                Estatutos 2026 (PDF)
              </a>
              <a
                href={
                  perfil?.documentos.utilidad_publica_pdf ??
                  'https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf'
                }
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-zinc-300 text-zinc-800 hover:border-[#6aa43a] hover:text-[#2d5a27] rounded-sm transition-colors"
              >
                <Building2 className="w-3.5 h-3.5 text-[#6aa43a]" />
                Utilidad Pública (PDF)
              </a>
              <a
                href={
                  perfil?.documentos.memoria_2024_pdf ??
                  'https://reforesta.es/wp-content/uploads/2026/05/Memoria-Reforesta-2024.pdf'
                }
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#2d5a27] text-white hover:bg-[#1e3d1a] rounded-sm transition-colors"
              >
                <FileText className="w-3.5 h-3.5" />
                Memoria Anual 2024 (PDF)
              </a>
            </div>
          </div>
        </section>
      </main>

      <ConvocatoriaDrawer
        convocatoria={convocatoriaSeleccionada}
        onClose={() => setConvocatoriaSeleccionada(null)}
        onCambiarEstado={handleCambiarEstado}
      />

      {/* Footer corporativo idéntico a https://reforesta.es/ */}
      <footer className="bg-[#191919] text-[#cccccc] mt-10 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid gap-8 md:grid-cols-4 text-sm">
          <div className="flex flex-col items-start">
            <a href="https://reforesta.es/" target="_blank" rel="noopener noreferrer">
              <img
                src="/reforesta/logo-reforesta-blanco-pie.png"
                alt="Reforesta"
                className="w-[140px] h-auto object-contain"
              />
            </a>
            <a
              href="https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-block text-[11px] uppercase tracking-wider text-[#7cc142] hover:underline font-semibold"
            >
              Declarada de Utilidad Pública ↗
            </a>
          </div>

          <div>
            <h4 className="text-white font-semibold text-base mb-2.5">Asociación Reforesta</h4>
            <p className="text-[12.5px] leading-relaxed text-[#b8b8b8]">
              ONG fundada en 1991 (NIF G80428204 · Registro Nacional nº 162965) para la conservación de los bosques y la
              lucha contra la desertificación. Sector Foresta 43, Oficina 33, 28760 Tres Cantos (Madrid).
            </p>
            <p className="mt-2.5 text-[12px] text-[#999999]">
              Contacto:{' '}
              <a href="mailto:info@reforesta.es" className="text-[#7cc142] hover:underline">
                info@reforesta.es
              </a>
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold text-base mb-2.5">Documentación y Fuentes</h4>
            <ul className="space-y-2 text-[12px]">
              <li className="border-b border-white/10 pb-1.5">
                <a
                  href="https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-[#7cc142] transition-colors font-medium block"
                >
                  Estatutos Oficiales de Reforesta (PDF)
                </a>
              </li>
              <li className="border-b border-white/10 pb-1.5">
                <a
                  href="https://reforesta.es/wp-content/uploads/2026/05/Memoria-Reforesta-2024.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white hover:text-[#7cc142] transition-colors font-medium block"
                >
                  Memoria de Actividades 2024 (PDF)
                </a>
              </li>
              <li className="text-[11px] text-zinc-400 pt-0.5">
                Radar diario 07:00h · BDNS · BOE · 19 Boletines CCAA · PLACSP · LIFE/SEDIA · Fundaciones RSC
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-base mb-2.5">Síguenos</h4>
            <div className="flex flex-wrap items-center gap-2">
              <a
                href="https://www.facebook.com/asociacion.reforesta"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Facebook"
                className="w-9 h-9 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-xs transition-colors"
              >
                f
              </a>
              <a
                href="https://twitter.com/Reforesta_ONG"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="X Twitter"
                className="w-9 h-9 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-xs transition-colors"
              >
                𝕏
              </a>
              <a
                href="https://www.instagram.com/reforesta_ong/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="w-9 h-9 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-[11px] transition-colors"
              >
                IG
              </a>
              <a
                href="https://www.youtube.com/c/Reforesta_ong"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="YouTube"
                className="w-9 h-9 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-[11px] transition-colors"
              >
                ▶
              </a>
              <a
                href="https://www.linkedin.com/company/asociacion-reforesta/"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                className="w-9 h-9 rounded-full bg-[#6aa43a] hover:bg-[#598c30] text-white flex items-center justify-center font-bold text-[11px] transition-colors"
              >
                in
              </a>
            </div>
          </div>
        </div>

        <div className="bg-[#111111] border-t border-white/10 py-3 px-4 sm:px-6 lg:px-8 text-xs text-zinc-400">
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
