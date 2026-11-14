import { Convocatoria, EstadoInterno } from '../types/convocatoria';

/**
 * Datos de EJEMPLO para visualizar el mapa territorial completo.
 * Para desactivarlos: ponga USAR_DATOS_MAPA_COMPLETO a false (o borre este archivo y su uso en mockConvocatorias.ts).
 */
export const USAR_DATOS_MAPA_COMPLETO = true;

// Comunidad (nombre igual al del GeoJSON) → nº de convocatorias de ejemplo
const POR_COMUNIDAD: Record<string, number> = {
  'Andalucía': 5,
  'Aragón': 2,
  'Principado de Asturias': 3,
  'Illes Balears': 1,
  'Canarias': 2,
  'Cantabria': 1,
  'Castilla-La Mancha': 4,
  'Cataluña': 4,
  'Comunitat Valenciana': 3,
  'Extremadura': 4,
  'La Rioja': 1,
  'Región de Murcia': 2,
  'Navarra': 2,
  'País Vasco': 3,
  'Galicia': 3,
  'Comunidad de Madrid': 1,
  'Castilla y León': 2,
};

const TEMAS = [
  { t: 'Restauración de riberas y bosque de galería', l: [92, 80, 60], acc: 'Plantación de especies autóctonas de ribera' },
  { t: 'Recuperación de áreas quemadas con frondosas autóctonas', l: [96, 70, 55], acc: 'Reforestación tras incendio con planta certificada' },
  { t: 'Conservación de hábitats y corredores ecológicos', l: [70, 94, 60], acc: 'Creación de charcas y refugios para fauna' },
  { t: 'Educación ambiental y voluntariado forestal', l: [55, 60, 93], acc: 'Jornadas escolares y voluntariado de plantación' },
  { t: 'Lucha contra la desertificación y la erosión', l: [90, 72, 58], acc: 'Plantación en laderas y control de erosión' },
  { t: 'Control de especies invasoras y regeneración natural', l: [74, 90, 62], acc: 'Retirada de invasoras y siembra de nativas' },
];

const ESTADOS: EstadoInterno[] = ['nueva', 'nueva', 'priorizada', 'en_preparacion', 'nueva', 'presentada'];

const fechaDesdeHoy = (dias: number) => {
  const d = new Date('2026-11-14T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + dias);
  return d.toISOString().slice(0, 10);
};

function generar(): Convocatoria[] {
  const salida: Convocatoria[] = [];
  let semilla = 11;
  const rnd = () => ((semilla = (semilla * 9301 + 49297) % 233280) / 233280);

  Object.entries(POR_COMUNIDAD).forEach(([comunidad, n]) => {
    for (let i = 0; i < n; i++) {
      const tema = TEMAS[Math.floor(rnd() * TEMAS.length)];
      const dias = 4 + Math.floor(rnd() * 55);
      const cuantia = (2 + Math.floor(rnd() * 14)) * 10000;
      const cofin = [0, 0, 10, 20][Math.floor(rnd() * 4)];
      const jitter = () => Math.round((rnd() - 0.5) * 12);
      const lineas = {
        restauracionEcosistemas: Math.min(99, tema.l[0] + jitter()),
        conservacionHabitats: Math.min(99, tema.l[1] + jitter()),
        educacionAmbiental: Math.min(99, tema.l[2] + jitter()),
      };
      const matching = Math.round((lineas.restauracionEcosistemas * 0.45 + lineas.conservacionHabitats * 0.35 + lineas.educacionAmbiental * 0.2));
      const slug = comunidad.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z]+/g, '-');
      const codigo = `EJEMPLO-${slug.slice(0, 4).toUpperCase()}-${i + 1}`;
      salida.push({
        id: `ejemplo-${slug}-${i + 1}`,
        codigoOficial: codigo,
        titulo: `${tema.t} · ${comunidad} (dato de ejemplo)`,
        organismo: `Consejería de Medio Ambiente · ${comunidad}`,
        tipoFuente: 'publica_autonomica',
        ambitoTerritorial: comunidad,
        presupuestoTotal: cuantia * 20,
        cuantiaMaximaProyecto: cuantia,
        porcentajeCofinanciacion: cofin,
        modalidadPago: cofin === 0 ? 'anticipo' : 'reembolso',
        fechaPublicacion: fechaDesdeHoy(-10),
        fechaCierre: fechaDesdeHoy(dias),
        diasRestantes: dias,
        urgencia: dias < 7 ? 'critica' : dias < 20 ? 'moderada' : 'holgada',
        elegible: true,
        motivoElegibilidad: 'Apta: admite entidades sin ánimo de lucro declaradas de utilidad pública.',
        dealbreakers: [],
        matchingGlobal: matching,
        matchingLineas: lineas,
        citasBasesJustificacion: ['Dato de ejemplo generado para previsualizar el mapa territorial.'],
        resumenEjecutivo: `Convocatoria de ejemplo en ${comunidad}: ${tema.t.toLowerCase()}. Generada solo para visualizar el mapa completo.`,
        accionesSubvencionables: [tema.acc],
        gastosNoSubvencionables: [],
        requisitosSolvencia: [],
        urlBasesPdf: 'https://example.com/bases.pdf',
        urlSedeElectronica: 'https://example.com',
        fuenteUrl: 'https://example.com',
        estadoInterno: ESTADOS[Math.floor(rnd() * ESTADOS.length)],
      });
    }
  });
  return salida;
}

export const MOCK_MAPA_COMPLETO: Convocatoria[] = generar();
