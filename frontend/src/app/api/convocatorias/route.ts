import { NextResponse } from 'next/server';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ambito = searchParams.get('ambito');
  const tipo = searchParams.get('tipo');
  const estado = searchParams.get('estado') || 'TODAS';
  const soloElegibles = searchParams.get('soloElegibles') === 'true';

  let results = [...MOCK_CONVOCATORIAS];
  let fuente = 'api_route_mock';

  try {
    const res = await fetch(`${BACKEND_URL}/api/convocatorias?estado=${encodeURIComponent(estado)}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data.convocatorias) && data.convocatorias.length > 0) {
        results = data.convocatorias;
        fuente = 'backend_diego';
      }
    }
  } catch {
    // Fallback to MOCK_CONVOCATORIAS if backend is offline
  }

  if (ambito && ambito !== 'todos') {
    results = results.filter((c) => c.ambitoTerritorial.toLowerCase().includes(ambito.toLowerCase()));
  }

  if (tipo && tipo !== 'todos') {
    results = results.filter((c) => c.tipoFuente === tipo);
  }

  if (soloElegibles) {
    results = results.filter((c) => c.elegible);
  }

  return NextResponse.json({
    total: results.length,
    convocatorias: results,
    fuente,
    actualizadoAt: new Date().toISOString(),
  });
}
