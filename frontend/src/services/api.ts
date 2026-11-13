import { Convocatoria } from '@/types/convocatoria';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface FetchConvocatoriasResponse {
  convocatorias: Convocatoria[];
  fuente: 'backend_diego' | 'api_route_mock' | 'fallback_local';
  timestamp: string;
}

export async function fetchConvocatorias(): Promise<FetchConvocatoriasResponse> {
  // 1. Intentar conectar con la API en vivo de Diego (FastAPI en rama back)
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 segundos timeout

    const res = await fetch(`${BACKEND_URL}/api/convocatorias`, {
      signal: controller.signal,
      cache: 'no-store',
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      return {
        convocatorias: data.convocatorias || data,
        fuente: 'backend_diego',
        timestamp: new Date().toISOString(),
      };
    }
  } catch {
    // Si no está corriendo el backend de Diego, pasamos al siguiente fallback
  }

  // 2. Intentar consumir la API Route interna de Next.js
  try {
    const res = await fetch('/api/convocatorias');
    if (res.ok) {
      const data = await res.json();
      return {
        convocatorias: data.convocatorias,
        fuente: 'api_route_mock',
        timestamp: data.actualizadoAt || new Date().toISOString(),
      };
    }
  } catch {
    // Fallback final
  }

  // 3. Fallback directo a los datos mock estáticos
  return {
    convocatorias: MOCK_CONVOCATORIAS,
    fuente: 'fallback_local',
    timestamp: new Date().toISOString(),
  };
}
