'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Feature, FeatureCollection } from 'geojson';
import { ArrowLeft } from 'lucide-react';
import { Convocatoria } from '@/types/convocatoria';
import { COMUNIDADES, TODOS, filtrarPorTerritorio, formatoEuros, perteneceAComunidad } from '@/lib/territorio';

interface LeafletMapProps {
  convocatorias: Convocatoria[];
  territorio: string;
  provincia: string;
  onCambiarTerritorio: (territorio: string) => void;
  onCambiarProvincia: (provincia: string) => void;
}

// Escala secuencial de un solo tono (verde Reforesta): 0 → blanco, más convocatorias → más intenso
const ESCALA = ['#ffffff', '#e0eecb', '#bcdc8f', '#8fbf55', '#4a7a29'];
const colorPorConteo = (n: number) => ESCALA[Math.min(n, ESCALA.length - 1)];

const BOUNDS_ESPANA = L.latLngBounds([27.5, -18.5], [44.2, 4.8]);
const BOUNDS_VISTA_INICIAL = L.latLngBounds([35.8, -9.6], [43.9, 4.4]);

export default function LeafletMap({ convocatorias, territorio, provincia, onCambiarTerritorio, onCambiarProvincia }: LeafletMapProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<L.Map | null>(null);
  const capasRef = useRef<L.LayerGroup | null>(null);
  const geoRef = useRef<{ ccaa: FeatureCollection; prov: FeatureCollection } | null>(null);
  const primeraVezRef = useRef(true);
  const cbRef = useRef({ onCambiarTerritorio, onCambiarProvincia });

  useEffect(() => {
    cbRef.current = { onCambiarTerritorio, onCambiarProvincia };
  });

  // Inicialización del mapa (una sola vez)
  useEffect(() => {
    if (!contenedorRef.current || mapaRef.current) return;

    const map = L.map(contenedorRef.current, {
      zoomControl: false,
      attributionControl: false,
      zoomDelta: 0.5,
      scrollWheelZoom: false, // la rueda sigue desplazando la página
      minZoom: 4,
      maxZoom: 10,
      maxBounds: BOUNDS_ESPANA.pad(0.6),
      zoomSnap: 0.25,
      center: [39.9, -3.4],
      zoom: contenedorRef.current.clientWidth < 600 ? 5 : 6,
    });
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    capasRef.current = L.layerGroup().addTo(map);
    mapaRef.current = map;

    const ro = new ResizeObserver(() => map.invalidateSize({ animate: false }));
    ro.observe(contenedorRef.current);
    return () => {
      ro.disconnect();
      map.remove();
      mapaRef.current = null;
      capasRef.current = null;
      primeraVezRef.current = true;
    };
  }, []);

  // Dibujo: comunidades (vista general) o provincias de la comunidad elegida
  useEffect(() => {
    const map = mapaRef.current;
    const capas = capasRef.current;
    if (!map || !capas) return;
    let cancelado = false;

    const pintar = ({ ccaa, prov }: { ccaa: FeatureCollection; prov: FeatureCollection }) => {
      if (cancelado) return;
      capas.clearLayers();
      const enComunidad = COMUNIDADES.includes(territorio);

      // --- Comunidades (la elegida se sustituye por sus provincias)
      const capaCcaa = L.geoJSON(ccaa, {
        filter: (f) => !(enComunidad && f.properties?.name === territorio),
        style: (f?: Feature) => {
          const n = filtrarPorTerritorio(convocatorias, f?.properties?.name as string).length;
          return {
            fillColor: enComunidad ? '#ebe9e1' : colorPorConteo(n),
            fillOpacity: 1,
            color: '#c7c7c7',
            weight: 0.8,
          };
        },
        onEachFeature: (feature, layer) => {
          const nombre = feature.properties?.name as string;
          const items = filtrarPorTerritorio(convocatorias, nombre);
          const euros = items.reduce((a, c) => a + c.cuantiaMaximaProyecto, 0);
          layer.bindTooltip(
            `<strong>${nombre}</strong><br/>${items.length === 0 ? 'Sin convocatorias' : `${items.length} ${items.length === 1 ? 'convocatoria' : 'convocatorias'} · ${formatoEuros(euros)}`}`,
            { sticky: true, className: 'tooltip-reforesta' }
          );
          layer.on({
            mouseover: (e) => (e.target as L.Path).setStyle({ weight: 1.5, color: '#494949' }),
            mouseout: (e) => (e.target as L.Path).setStyle({ weight: 0.8, color: '#c7c7c7' }),
            click: () => cbRef.current.onCambiarTerritorio(nombre),
          });
        },
      }).addTo(capas);

      // --- Provincias de la comunidad elegida
      let capaProv: L.GeoJSON | null = null;
      if (enComunidad) {
        capaProv = L.geoJSON(prov, {
          filter: (f) => f.properties?.ccaa === territorio,
          style: (f?: Feature) => {
            const nombre = f?.properties?.name as string;
            const n = convocatorias.filter((c) => c.provincia === nombre && perteneceAComunidad(c.ambitoTerritorial, territorio)).length;
            const activa = provincia === nombre;
            return {
              fillColor: colorPorConteo(n),
              fillOpacity: 1,
              color: activa ? '#212121' : '#6b6b66',
              weight: activa ? 3 : 1.2,
            };
          },
          onEachFeature: (feature, layer) => {
            const nombre = feature.properties?.name as string;
            const propias = convocatorias.filter((c) => c.provincia === nombre && perteneceAComunidad(c.ambitoTerritorial, territorio));
            const euros = propias.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0);
            layer.bindTooltip(
              `<strong>${nombre}</strong><br/>${propias.length === 0 ? 'Sin convocatorias propias' : `${propias.length} ${propias.length === 1 ? 'convocatoria propia' : 'convocatorias propias'} · ${formatoEuros(euros)}`}`,
              { sticky: true, className: 'tooltip-reforesta' }
            );
            // Etiqueta permanente con el nombre (marcador aparte: una capa solo admite un tooltip)
            const centro = (layer as L.Polygon).getBounds().getCenter();
            L.marker(centro, {
              interactive: false,
              icon: L.divIcon({ className: 'etiqueta-provincia', html: `<span class="etq">${nombre}${propias.length ? `<br/><small>${propias.length}</small>` : ''}</span>`, iconSize: [0, 0] }),
            }).addTo(capas);
            layer.on({
              mouseover: (e) => (e.target as L.Path).setStyle({ weight: 2.5, color: '#212121' }),
              mouseout: (e) => capaProv?.resetStyle(e.target as L.Path),
              click: () => cbRef.current.onCambiarProvincia(provincia === nombre ? '' : nombre),
            });
          },
        }).addTo(capas);
      }

      // --- Encuadre: zoom animado a la comunidad, o vista general
      const objetivo = capaProv && capaProv.getBounds().isValid() ? capaProv.getBounds() : BOUNDS_VISTA_INICIAL;
      if (primeraVezRef.current) {
        map.fitBounds(objetivo, { animate: false });
        primeraVezRef.current = false;
      } else {
        map.flyToBounds(objetivo, { padding: [24, 24], duration: 0.9 });
      }
      void capaCcaa;
    };

    if (geoRef.current) {
      pintar(geoRef.current);
    } else {
      Promise.all([
        fetch('/data/ccaa.geojson').then((r) => r.json() as Promise<FeatureCollection>),
        fetch('/data/provincias.geojson').then((r) => r.json() as Promise<FeatureCollection>),
      ]).then(([ccaa, prov]) => {
        geoRef.current = { ccaa, prov };
        pintar(geoRef.current);
      });
    }
    return () => {
      cancelado = true;
    };
  }, [convocatorias, territorio, provincia]);

  const enComunidad = COMUNIDADES.includes(territorio);

  return (
    <div className="relative w-full h-[560px] border border-zinc-200 overflow-hidden isolate bg-[#e6ebe3]">
      <div ref={contenedorRef} className="w-full h-full !bg-transparent" />

      {enComunidad && (
        <button
          onClick={() => onCambiarTerritorio(TODOS)}
          className="absolute top-3 left-3 z-[500] flex items-center gap-2 rounded-full bg-white border border-zinc-300 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-900 hover:bg-zinc-900 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> España
        </button>
      )}

      {/* Leyenda */}
      <div className="absolute top-3 right-3 z-[500] bg-white/95 border border-zinc-200 px-3 py-2 text-xs text-zinc-600">
        <span className="block font-semibold text-zinc-900 mb-1">{enComunidad ? 'Convocatorias propias' : 'Convocatorias'}</span>
        <div className="flex items-center gap-1">
          {ESCALA.map((c, i) => (
            <span key={c} className="flex flex-col items-center gap-0.5">
              <span className="h-2.5 w-5 border border-zinc-200" style={{ background: c }} />
              <span>{i === ESCALA.length - 1 ? `${i}+` : i}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
