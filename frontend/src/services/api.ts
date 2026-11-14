import { normalizarPlazos } from '@/lib/plazo';
import { Convocatoria, EstadoInterno } from '@/types/convocatoria';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';
import { ESTATAL, PROVINCIAS_POR_COMUNIDAD } from '@/lib/territorio';
import { humanizar } from '@/lib/texto';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Código ISO de comunidad que usa el backend → nombre que usa el mapa. */
const CCAA_POR_CODIGO: Record<string, string> = {
  'ES-AN': 'Andalucía', 'ES-AR': 'Aragón', 'ES-AS': 'Principado de Asturias', 'ES-CB': 'Cantabria',
  'ES-CE': 'Ceuta', 'ES-CL': 'Castilla y León', 'ES-CM': 'Castilla-La Mancha', 'ES-CN': 'Canarias',
  'ES-CT': 'Cataluña', 'ES-EX': 'Extremadura', 'ES-GA': 'Galicia', 'ES-IB': 'Illes Balears',
  'ES-MC': 'Región de Murcia', 'ES-MD': 'Comunidad de Madrid', 'ES-ML': 'Melilla',
  'ES-NC': 'Navarra', 'ES-PV': 'País Vasco', 'ES-RI': 'La Rioja', 'ES-VC': 'Comunitat Valenciana',
};

const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

/** Forma de una convocatoria tal y como la envía el backend (campos extra respecto al contrato base). */
type ConvocatoriaApi = Partial<Convocatoria> & {
  ccaaCodigo?: string;
  nivelTerritorial?: string;
  ubicacion?: { ccaa_nombre?: string | null; provincia_nombre?: string | null };
};

/** Convierte el payload del backend al contrato del front: ámbito = comunidad (o Estatal) y provincia aparte. */
export function adaptarConvocatoria(raw: ConvocatoriaApi): Convocatoria {
  const codigo = raw.ccaaCodigo ?? '';
  const comunidad = CCAA_POR_CODIGO[codigo] ?? (codigo && codigo !== 'ES' && codigo !== 'EU' ? raw.ubicacion?.ccaa_nombre ?? undefined : undefined);
  const ambitoTerritorial = comunidad ?? ESTATAL;

  // Provincia: solo si la comunidad es pluriprovincial y el nombre del backend casa con una de sus provincias
  let provincia: string | undefined;
  const provBackend = raw.ubicacion?.provincia_nombre;
  const lista = comunidad ? PROVINCIAS_POR_COMUNIDAD[comunidad] : undefined;
  if (provBackend && lista) {
    const n = normalizar(provBackend);
    provincia = lista.find((p) => n.includes(normalizar(p)) || normalizar(p).includes(n.split('/')[0].trim()));
  }

  return {
    ...(raw as Convocatoria),
    ambitoTerritorial,
    provincia,
    dealbreakers: raw.dealbreakers ?? [],
    citasBasesJustificacion: raw.citasBasesJustificacion ?? [],
    accionesSubvencionables: (raw.accionesSubvencionables ?? []).map(humanizar),
    orografiaPendiente: raw.orografiaPendiente ? humanizar(raw.orografiaPendiente) : undefined,
    motivoElegibilidad: humanizar(raw.motivoElegibilidad),
    resumenEjecutivo: humanizar(raw.resumenEjecutivo),
    matchingGlobal: Math.round(raw.matchingGlobal ?? 0),
  };
}

export interface FetchConvocatoriasResponse {
  convocatorias: Convocatoria[];
  /** 'backend' = datos reales del radar; 'ejemplo' = backend no disponible, datos de demostración */
  fuente: 'backend' | 'ejemplo';
  timestamp: string;
}

export async function fetchConvocatorias(): Promise<FetchConvocatoriasResponse> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 6000);
    const res = await fetch(`${BACKEND_URL}/api/convocatorias`, { signal: controller.signal, cache: 'no-store' });
    clearTimeout(timeout);
    if (res.ok) {
      const data = await res.json();
      const lista: ConvocatoriaApi[] = data.convocatorias ?? data;
      return {
        convocatorias: normalizarPlazos(lista.map(adaptarConvocatoria), false),
        fuente: 'backend',
        timestamp: data.actualizadoAt ?? new Date().toISOString(),
      };
    }
  } catch {
    // backend no disponible: se avisa en la interfaz y se usan los datos de ejemplo
  }
  return { convocatorias: normalizarPlazos(MOCK_CONVOCATORIAS, true), fuente: 'ejemplo', timestamp: new Date().toISOString() };
}

/**
 * Histórico completo (activas + cerradas, 2020 en adelante) para la sección de búsqueda y la previsión de recurrencia.
 * `disponible = false` cuando el backend no responde: no hay datos de ejemplo para el histórico.
 */
export async function fetchHistorico(): Promise<{ convocatorias: Convocatoria[]; disponible: boolean }> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    const res = await fetch(`${BACKEND_URL}/api/convocatorias?estado=TODAS`, { signal: controller.signal, cache: 'no-store' });
    clearTimeout(timeout);
    if (res.ok) {
      const data = await res.json();
      const lista: ConvocatoriaApi[] = data.convocatorias ?? data;
      return { convocatorias: normalizarPlazos(lista.map(adaptarConvocatoria), false), disponible: true };
    }
  } catch {
    // sin backend: la sección lo indica
  }
  return { convocatorias: [], disponible: false };
}

/** Cifras reales de la última ingesta del radar (para el embudo de la portada). */
export interface EmbudoReal {
  detectadas: number;
  pasaronFiltro: number;
  aceptadas: number;
  ultimaIngesta: string | null;
  /** Próxima sincronización automática del backend (ISO), si la informa */
  proximaSincronizacion: string | null;
}

export async function fetchEmbudo(): Promise<EmbudoReal | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/ingest/runs?limit=1`, { cache: 'no-store' });
    if (!res.ok) return null;
    const payload = await res.json();
    const run = payload.runs?.[0];
    if (!run) return null;
    return {
      detectadas: run.total_scanned ?? 0,
      pasaronFiltro: run.passed_layer1 ?? 0,
      aceptadas: run.accepted_layer2 ?? 0,
      ultimaIngesta: run.finished_at ?? run.started_at ?? null,
      proximaSincronizacion: payload.next_daily_sync_at ?? null,
    };
  } catch {
    return null;
  }
}

/** Persiste el estado interno (pipeline) en el backend. Devuelve false si no se pudo. */
export async function actualizarEstadoBackend(id: string, estadoInterno: EstadoInterno): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/convocatorias/${encodeURIComponent(id)}/estado`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estadoInterno }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
