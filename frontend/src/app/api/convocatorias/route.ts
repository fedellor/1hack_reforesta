import { NextResponse } from 'next/server';

// En Docker el servidor de Next llega al backend por su nombre de servicio (BACKEND_INTERNAL_URL); en local, por localhost
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

/** Proxy del backend (sin datos de respaldo): reenvía `estado` y devuelve 502 si el radar no responde. */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const estado = searchParams.get('estado') || 'TODAS';
  try {
    const res = await fetch(`${BACKEND_URL}/api/convocatorias?estado=${encodeURIComponent(estado)}`, { cache: 'no-store' });
    if (!res.ok) return NextResponse.json({ error: 'backend_error', status: res.status }, { status: 502 });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: 'backend_no_disponible' }, { status: 502 });
  }
}
