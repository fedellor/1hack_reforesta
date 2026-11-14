'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Feature, FeatureCollection } from 'geojson';
import { Convocatoria } from '@/types/convocatoria';
import { TODOS, filtrarPorTerritorio, formatoEuros } from '@/lib/territorio';

interface LeafletMapProps {
  convocatorias: Convocatoria[];
  territorio: string;
  onCambiarTerritorio: (territorio: string) => void;
}

// Escala secuencial de un solo tono (verde Reforesta): 0 → neutro, más convocatorias → más intenso
const ESCALA = ['#ffffff', '#e0eecb', '#bcdc8f', '#8fbf55', '#4a7a29'];
const colorPorConteo = (n: number) => ESCALA[Math.min(n, ESCALA.length - 1)];

const BOUNDS_ESPANA = L.latLngBounds([27.5, -18.5], [44.2, 4.8]);

export default function LeafletMap({ convocatorias, territorio, onCambiarTerritorio }: LeafletMapProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<L.Map | null>(null);
  const capaRef = useRef<L.GeoJSON | null>(null);
  const geoRef = useRef<FeatureCollection | null>(null);
  const callbackRef = useRef(onCambiarTerritorio);

  const porComunidad = (nombre: string) => {
    const items = filtrarPorTerritorio(convocatorias, nombre);
    return { n: items.length, euros: items.reduce((acc, c) => acc + c.cuantiaMaximaProyecto, 0) };
  };
  const porComunidadRef = useRef(porComunidad);

  useEffect(() => {
    callbackRef.current = onCambiarTerritorio;
    porComunidadRef.current = porComunidad;
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

    // Sin teselas externas: solo los límites autonómicos sobre fondo liso (funciona offline)
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    mapaRef.current = map;
    // Reajustar al tamaño real del contenedor (cambio de vista, layout, resize)
    const el = contenedorRef.current;
    const ro = new ResizeObserver(() => {
      map.invalidateSize({ animate: false });
      // Reproyectar las regiones si se dibujaron con otro zoom/tamaño
      const capa = capaRef.current;
      if (capa) {
        map.removeLayer(capa);
        map.addLayer(capa);
      }
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      map.remove();
      mapaRef.current = null;
      capaRef.current = null;
    };
  }, []);

  // Capa coroplética por comunidad autónoma
  useEffect(() => {
    const map = mapaRef.current;
    if (!map) return;
    let cancelado = false;

    const pintar = (geo: FeatureCollection) => {
      capaRef.current?.remove();
      const estilo = (f?: Feature) => {
        const nombre = f?.properties?.name as string;
        const { n } = porComunidadRef.current(nombre);
        const activa = territorio === nombre;
        return {
          fillColor: colorPorConteo(n),
          fillOpacity: 1,
          color: activa ? '#212121' : '#c7c7c7',
          weight: activa ? 2 : 0.8,
        };
      };
      const capa = L.geoJSON(geo, {
        style: estilo,
        onEachFeature: (feature, layer) => {
          const nombre = feature.properties?.name as string;
          const { n, euros } = porComunidadRef.current(nombre);
          layer.bindTooltip(
            `<strong>${nombre}</strong><br/>${n === 0 ? 'Sin convocatorias' : `${n} ${n === 1 ? 'convocatoria' : 'convocatorias'} · ${formatoEuros(euros)}`}`,
            { sticky: true, className: 'tooltip-reforesta' }
          );
          layer.on({
            mouseover: (e) => (e.target as L.Path).setStyle({ weight: 1.5, color: '#494949' }),
            mouseout: () => capa.resetStyle(layer as L.Path),
            click: () => callbackRef.current(territorio === nombre ? TODOS : nombre),
          });
        },
      }).addTo(map);
      capaRef.current = capa;
    };

    if (geoRef.current) {
      pintar(geoRef.current);
    } else {
      fetch('/data/ccaa.geojson')
        .then((r) => r.json())
        .then((geo: FeatureCollection) => {
          geoRef.current = geo;
          if (!cancelado) pintar(geo);
        });
    }
    return () => {
      cancelado = true;
    };
  }, [convocatorias, territorio]);

  return (
    <div className="relative w-full h-[520px] rounded-lg border border-zinc-200 overflow-hidden isolate bg-[#e6ebe3]">
      <div ref={contenedorRef} className="w-full h-full !bg-transparent" />

      {/* Leyenda */}
      <div className="absolute top-3 right-3 z-[500] bg-white/95 border border-zinc-200 rounded-md px-2.5 py-2 text-[10px] text-zinc-600 shadow-2xs">
        <span className="block font-medium text-zinc-900 mb-1">Convocatorias</span>
        <div className="flex items-center gap-1">
          {ESCALA.map((c, i) => (
            <span key={c} className="flex flex-col items-center gap-0.5">
              <span className="h-2.5 w-5 rounded-sm border border-zinc-200" style={{ background: c }} />
              <span>{i === ESCALA.length - 1 ? `${i}+` : i}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
