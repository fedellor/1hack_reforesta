import { NextResponse } from 'next/server';
import { MOCK_CONVOCATORIAS } from '@/data/mockConvocatorias';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ambito = searchParams.get('ambito');
  const tipo = searchParams.get('tipo');
  const soloElegibles = searchParams.get('soloElegibles') === 'true';

  let results = [...MOCK_CONVOCATORIAS];

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
    actualizadoAt: new Date().toISOString(),
  });
}
