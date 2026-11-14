export type TipoFuente = 'publica_estatal' | 'publica_autonomica' | 'europea' | 'privada_rsc';

export type UrgenciaPlazo = 'critica' | 'moderada' | 'holgada'; // <7d, <20d, >20d

export type EstadoInterno = 'nueva' | 'priorizada' | 'en_preparacion' | 'presentada' | 'descartada';

export interface MatchingLineas {
  restauracionEcosistemas: number; // 0 - 100 (charcas, plantación autóctona, desertificación)
  conservacionHabitats: number;    // 0 - 100 (tritón ibérico, ailanto, Guadarrama)
  educacionAmbiental: number;      // 0 - 100 (voluntariado, sensibilización)
}

export interface Convocatoria {
  id: string;
  codigoOficial: string;          // Ej: "BDNS 923290" u "Orden 1689/2026"
  titulo: string;
  tituloOriginal?: string;
  organismo: string;              // Ej: "MITECO", "Comunidad de Madrid", "Fundación Santander"
  tipoFuente: TipoFuente;
  ambitoTerritorial: string;      // "Estatal", "Comunidad de Madrid", "Galicia", "Castilla y León", etc.
  provincia?: string;             // Solo si la convocatoria es provincial (p. ej. diputaciones); si falta, aplica a toda la comunidad
  orografiaPendiente?: string;    // "Pendiente pronunciada (>20%)", "Media ladera", "Llanura / Ribera"
  
  // Finanzas
  presupuestoTotal?: number;
  cuantiaMaximaProyecto: number;
  porcentajeCofinanciacion: number; // 0 significa 100% financiado / 0% fondos propios
  modalidadPago: 'anticipo' | 'reembolso' | 'mixto';

  // Plazos
  fechaPublicacion: string;
  fechaCierre: string;
  diasRestantes: number;
  urgencia: UrgenciaPlazo;

  // Elegibilidad y Scoring Reforesta
  elegible: boolean;
  motivoElegibilidad: string;     // Ej: "Apta: admite asociaciones sin ánimo de lucro declaradas de utilidad pública"
  dealbreakers: string[];         // Requisitos excluyentes detectados (si los hay)
  
  matchingGlobal: number;         // 0 - 100
  matchingLineas: MatchingLineas;
  citasBasesJustificacion: string[]; // Frases literales extraídas del PDF

  // Contenido de la Ficha Ejecutiva
  resumenEjecutivo: string;
  accionesSubvencionables: string[];
  gastosNoSubvencionables?: string[];
  requisitosSolvencia?: string[];

  // Trazabilidad
  urlBasesPdf: string;
  urlSedeElectronica: string;
  fuenteUrl: string;

  // Estado Interno Reforesta
  estadoInterno: EstadoInterno;

  // Metadatos enriquecidos del Backend (Ubicación, Plazos LPACAP Art. 30, Dinero)
  ccaaCodigo?: string;
  nivelTerritorial?: string;
  estado?: string;
  anio?: number;
  pagoAnticipadoSinAval?: boolean | null;
  diasHabilesRestantes?: number | null;
  ubicacion?: Record<string, unknown>;
  plazos?: Record<string, unknown>;
  dinero?: Record<string, unknown>;
}

export type FiltroElegibilidad = 'aptas' | 'excluidas';

export interface FiltrosState {
  busqueda: string;
  ambito: string;
  tipoFuente: string;
  elegibilidad: FiltroElegibilidad;
  minMatching: number;
  soloUrgentes: boolean;
  minCuantia: number;
  provincia: string;   // '' = sin provincia elegida
  ventanaDias: number; // 0 = sin límite; 30 = solo convocatorias que cierran en los próximos 30 días
  anio: number;        // 0 = todos los años (usado en Histórico desde 2016)
}
