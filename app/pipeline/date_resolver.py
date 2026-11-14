"""Spanish Administrative Date Parser and Business-Day Deadline Resolver."""
import re
from dataclasses import dataclass
from datetime import date, timedelta
from app.config import settings

SPANISH_MONTHS: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

NUMBER_WORDS: dict[str, int] = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "doce": 12,
    "quince": 15,
    "veinte": 20,
    "treinta": 30,
}

# Fixed national holidays in Spain (MM, DD)
FIXED_HOLIDAYS_ES: set[tuple[int, int]] = {
    (1, 1),    # Año Nuevo
    (1, 6),    # Epifanía del Señor
    (5, 1),    # Fiesta del Trabajo
    (8, 15),   # Asunción de la Virgen
    (10, 12),  # Fiesta Nacional de España
    (11, 1),   # Todos los Santos
    (12, 6),   # Día de la Constitución
    (12, 8),   # Inmaculada Concepción
    (12, 25),  # Natividad del Señor
}


@dataclass
class ResolvedDates:
    anio_convocatoria: int
    fecha_publicacion: date | None
    fecha_inicio_solicitud: date | None
    fecha_fin_solicitud: date | None
    plazo_texto_original: str | None
    es_plazo_calculado: bool
    estado: str  # ACTIVA | PROXIMA | CERRADA
    dias_restantes: int | None


def is_business_day_es(d: date) -> bool:
    """Return True if d is a working day (día hábil) in Spain."""
    if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    if (d.month, d.day) in FIXED_HOLIDAYS_ES:
        return False
    return True


def add_business_days(start_date: date, num_days: int) -> date:
    """Add Spanish business days (días hábiles) to start_date."""
    current = start_date
    remaining = max(0, num_days)
    while remaining > 0:
        current += timedelta(days=1)
        if is_business_day_es(current):
            remaining -= 1
    return current


def parse_spanish_date(text: str | date | None) -> date | None:
    """Parse ISO, DD/MM/YYYY, YYYY.MM.DD, or '11 de julio de 2024' formats."""
    if isinstance(text, date):
        return text
    if not text or not isinstance(text, str):
        return None
    s = text.strip()

    # 1. ISO YYYY-MM-DD or YYYY.MM.DD
    m_iso = re.search(r"\b(20\d{2})[-./](\d{1,2})[-./](\d{1,2})\b", s)
    if m_iso:
        try:
            return date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        except ValueError:
            pass

    # 2. DD/MM/YYYY or DD-MM-YYYY
    m_dmy = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b", s)
    if m_dmy:
        try:
            return date(int(m_dmy.group(3)), int(m_dmy.group(2)), int(m_dmy.group(1)))
        except ValueError:
            pass

    # 3. Textual: "20 de julio de 2023"
    m_txt = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(?:de\s+|del\s+)?(20\d{2})\b",
        s.lower(),
    )
    if m_txt:
        month = SPANISH_MONTHS.get(m_txt.group(2))
        if month:
            try:
                return date(int(m_txt.group(3)), month, int(m_txt.group(1)))
            except ValueError:
                pass

    return None


def _parse_int_or_word(token: str) -> int | None:
    token_clean = token.strip().lower()
    if token_clean.isdigit():
        return int(token_clean)
    return NUMBER_WORDS.get(token_clean)


def resolve_deadline_from_text(
    base_date: date,
    plazo_text: str,
) -> tuple[date | None, date | None, bool]:
    """
    Given a publication/registration date and a Spanish deadline clause,
    compute (fecha_inicio, fecha_fin, es_calculado).
    """
    if not plazo_text:
        return None, None, False

    direct_end = parse_spanish_date(plazo_text)
    if direct_end:
        return base_date, direct_end, False

    lower = plazo_text.lower()
    start_date = base_date + timedelta(days=1) if "siguiente" in lower else base_date

    # Check business days ("15 días hábiles", "diez días hábiles")
    m_habiles = re.search(
        r"\b(\d+|un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|doce|quince|veinte|treinta)\s+d[ií]as\s+h[aá]biles",
        lower,
    )
    if m_habiles:
        n = _parse_int_or_word(m_habiles.group(1))
        if n:
            end_date = add_business_days(base_date, n)
            return start_date, end_date, True

    # Check calendar days ("20 días naturales", "30 días")
    m_naturales = re.search(
        r"\b(\d+|diez|quince|veinte|treinta)\s+d[ií]as(?:\s+naturales)?",
        lower,
    )
    if m_naturales:
        n = _parse_int_or_word(m_naturales.group(1))
        if n:
            end_date = start_date + timedelta(days=n)
            return start_date, end_date, True

    # Check months ("un mes", "dos meses", "1 mes")
    m_meses = re.search(
        r"\b(\d+|un|uno|una|dos|tres|seis)\s+mes(?:es)?\b",
        lower,
    )
    if m_meses:
        n = _parse_int_or_word(m_meses.group(1))
        if n:
            end_date = start_date + timedelta(days=30 * n)
            return start_date, end_date, True

    return None, None, False


def compute_dates_and_status(
    fecha_publicacion: date | str | None = None,
    fecha_inicio_solicitud: date | str | None = None,
    fecha_fin_solicitud: date | str | None = None,
    plazo_texto_original: str | None = None,
    anio_hint: int | None = None,
    today: date | None = None,
) -> ResolvedDates:
    """Resolve all dates, status (ACTIVA/PROXIMA/CERRADA) and remaining days."""
    ref_today = today or settings.get_today()
    f_pub = parse_spanish_date(fecha_publicacion)
    f_ini = parse_spanish_date(fecha_inicio_solicitud)
    f_fin = parse_spanish_date(fecha_fin_solicitud)
    es_calculado = False

    if f_pub and not f_fin and plazo_texto_original:
        calc_ini, calc_fin, calc_flag = resolve_deadline_from_text(
            f_pub, plazo_texto_original
        )
        if not f_ini and calc_ini:
            f_ini = calc_ini
        if calc_fin:
            f_fin = calc_fin
            es_calculado = calc_flag

    anio = (
        anio_hint
        or (f_pub.year if f_pub else None)
        or (f_fin.year if f_fin else None)
        or ref_today.year
    )

    # Calculate status & dias_restantes
    if f_fin:
        delta = (f_fin - ref_today).days
        if f_ini and f_ini > ref_today:
            estado = "PROXIMA"
            dias_restantes = delta
        elif delta >= 0:
            estado = "ACTIVA"
            dias_restantes = delta
        else:
            estado = "CERRADA"
            dias_restantes = 0
    else:
        # If no closing date is fixed yet, active only if current/future year call
        if anio >= ref_today.year:
            estado = "ACTIVA"
            dias_restantes = None
        else:
            estado = "CERRADA"
            dias_restantes = 0

    return ResolvedDates(
        anio_convocatoria=anio,
        fecha_publicacion=f_pub,
        fecha_inicio_solicitud=f_ini,
        fecha_fin_solicitud=f_fin,
        plazo_texto_original=plazo_texto_original,
        es_plazo_calculado=es_calculado,
        estado=estado,
        dias_restantes=dias_restantes,
    )
