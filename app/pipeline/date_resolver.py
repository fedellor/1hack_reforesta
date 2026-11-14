"""Spanish Administrative Date Parser & LPACAP Art. 30 Business-Day Deadline Resolver (National + 19 CCAA Holidays)."""
import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta
from app.config import settings

SPANISH_MONTHS: dict[str, int] = {
    # Spanish
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
    # Catalan
    "gener": 1,
    "febrer": 2,
    "març": 3,
    "marc": 3,
    "maig": 5,
    "juny": 6,
    "juliol": 7,
    "setembre": 9,
    "novembre": 11,
    "desembre": 12,
    # Galician
    "xaneiro": 1,
    "febreiro": 2,
    "abril": 4,
    "xuno": 6,
    "xuño": 6,
    "xullo": 7,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "decembro": 12,
    # English
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
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
    "veinticinco": 25,
    "treinta": 30,
    "dues": 2,
    "dez": 10,
    "vint": 20,
    "trenta": 30,
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

# Autonomous Community specific holidays (MM, DD) for accurate regional bulletin deadlines
CCAA_HOLIDAYS: dict[str, set[tuple[int, int]]] = {
    "ES-AN": {(2, 28)},                  # Día de Andalucía
    "ES-AR": {(4, 23)},                  # San Jorge / Día de Aragón
    "ES-AS": {(9, 8)},                   # Día de Asturias
    "ES-CB": {(7, 28), (9, 15)},         # Día de las Instituciones / La Bien Aparecida
    "ES-CE": {(8, 5), (9, 2)},           # Virgen de África / Día de Ceuta
    "ES-CL": {(4, 23)},                  # Día de Castilla y León
    "ES-CM": {(5, 31)},                  # Día de Castilla-La Mancha
    "ES-CN": {(5, 30)},                  # Día de Canarias
    "ES-CT": {(6, 24), (9, 11), (12, 26)},  # Sant Joan, Diada, Sant Esteve
    "ES-EX": {(9, 8)},                   # Día de Extremadura
    "ES-GA": {(5, 17), (7, 25)},         # Día das Letras Galegas, Día Nacional de Galicia
    "ES-IB": {(3, 1)},                   # Dia de les Illes Balears
    "ES-MC": {(3, 19), (6, 9)},          # San José, Día de la Región de Murcia
    "ES-MD": {(5, 2), (5, 15), (11, 9)}, # Fiesta Comunidad de Madrid, San Isidro, La Almudena
    "ES-ML": {(9, 8), (9, 17)},          # Virgen de la Victoria, Día de Melilla
    "ES-NC": {(12, 3)},                  # San Francisco Javier / Día de Navarra
    "ES-PV": {(7, 25)},                  # Santiago Apóstol
    "ES-RI": {(6, 9)},                   # Día de La Rioja
    "ES-VC": {(3, 19), (6, 24), (10, 9)},# Fallas/San José, Sant Joan, Nou d'Octubre
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


def is_business_day_es(d: date, ccaa_codigo: str | None = None) -> bool:
    """
    Return True if d is a working day (día hábil) under Ley 39/2015 (LPACAP Art. 30.2),
    accounting for Saturdays, Sundays, national holidays, Sunday->Monday transfers, and CCAA holidays.
    """
    if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    holidays = set(FIXED_HOLIDAYS_ES)
    if ccaa_codigo and ccaa_codigo.upper() in CCAA_HOLIDAYS:
        holidays |= CCAA_HOLIDAYS[ccaa_codigo.upper()]

    if (d.month, d.day) in holidays:
        return False

    # If yesterday was Sunday and a holiday, Monday is often a transferred non-working day (lunes festivo)
    if d.weekday() == 0:
        yesterday = d - timedelta(days=1)
        if (yesterday.month, yesterday.day) in holidays:
            return False

    return True


def roll_to_next_business_day(d: date, ccaa_codigo: str | None = None) -> date:
    """
    LPACAP Art. 30.5: 'Cuando el último día del plazo sea inhábil,
    se entenderá prorrogado al primer día hábil siguiente.'
    """
    current = d
    while not is_business_day_es(current, ccaa_codigo=ccaa_codigo):
        current += timedelta(days=1)
    return current


def add_business_days(
    start_date: date,
    num_days: int,
    ccaa_codigo: str | None = None,
) -> date:
    """Add Spanish business days (días hábiles) to start_date."""
    current = start_date
    remaining = max(0, num_days)
    while remaining > 0:
        current += timedelta(days=1)
        if is_business_day_es(current, ccaa_codigo=ccaa_codigo):
            remaining -= 1
    return current


def count_business_days_remaining(
    start_date: date,
    end_date: date,
    ccaa_codigo: str | None = None,
) -> int:
    """
    Count working days (días hábiles LPACAP Art. 30.2) remaining from start_date to end_date,
    discounting Saturdays, Sundays, national holidays, Sunday->Monday transfers, and CCAA holidays.
    """
    if end_date <= start_date:
        return 0
    delta_days = (end_date - start_date).days
    if delta_days > 366:
        # Fast approximation for multi-year horizons (>1 year)
        return round(delta_days * 5 / 7)
    count = 0
    cur = start_date
    while cur < end_date:
        cur += timedelta(days=1)
        if is_business_day_es(cur, ccaa_codigo=ccaa_codigo):
            count += 1
    return count


def add_months_lpacap(
    base_date: date,
    months: int,
    ccaa_codigo: str | None = None,
) -> date:
    """
    LPACAP Art. 30.4: Plazos fijados en meses se computan de fecha a fecha.
    Si en el mes de vencimiento no hubiera día equivalente, expira el último día del mes,
    y si cae en inhábil se prorroga al primer día hábil siguiente (Art. 30.5).
    """
    total_month = base_date.month - 1 + max(1, months)
    target_year = base_date.year + total_month // 12
    target_month = total_month % 12 + 1
    max_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(base_date.day, max_day)
    end_date = date(target_year, target_month, target_day)
    return roll_to_next_business_day(end_date, ccaa_codigo=ccaa_codigo)


def parse_spanish_date(text: str | date | None) -> date | None:
    """Parse ISO, DD/MM/YYYY, DD.MM.YYYY, or multilingual textual dates (ES/CA/GL/EN)."""
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

    # 2. DD/MM/YYYY, DD-MM-YYYY or DD.MM.YYYY
    m_dmy = re.search(r"\b(\d{1,2})[-./](\d{1,2})[-./](20\d{2})\b", s)
    if m_dmy:
        try:
            return date(int(m_dmy.group(3)), int(m_dmy.group(2)), int(m_dmy.group(1)))
        except ValueError:
            pass

    # 3. Textual ES/CA/GL: "20 de julio de 2023", "15 d'octubre de 2026", "10 de outono/outubro do 2026"
    m_txt = re.search(
        r"\b(\d{1,2})\s+(?:de\s+|d['’])([a-záéíóúñç]+)\s+(?:de\s+|del\s+|do\s+)?(20\d{2})\b",
        s.lower(),
    )
    if m_txt:
        month = SPANISH_MONTHS.get(m_txt.group(2))
        if month:
            try:
                return date(int(m_txt.group(3)), month, int(m_txt.group(1)))
            except ValueError:
                pass

    # 4. English textual: "15 November 2026" or "November 15, 2026"
    m_en1 = re.search(r"\b(\d{1,2})\s+([a-z]+)\s+(20\d{2})\b", s.lower())
    if m_en1:
        month = SPANISH_MONTHS.get(m_en1.group(2))
        if month:
            try:
                return date(int(m_en1.group(3)), month, int(m_en1.group(1)))
            except ValueError:
                pass

    m_en2 = re.search(r"\b([a-z]+)\s+(\d{1,2}),?\s+(20\d{2})\b", s.lower())
    if m_en2:
        month = SPANISH_MONTHS.get(m_en2.group(1))
        if month:
            try:
                return date(int(m_en2.group(3)), month, int(m_en2.group(2)))
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
    ccaa_codigo: str | None = None,
) -> tuple[date | None, date | None, bool]:
    """
    Given a publication/registration date and a Spanish deadline clause,
    compute (fecha_inicio, fecha_fin, es_calculado) under LPACAP Art. 30 rules.
    """
    if not plazo_text:
        return None, None, False

    direct_end = parse_spanish_date(plazo_text)
    if direct_end:
        return base_date, roll_to_next_business_day(direct_end, ccaa_codigo=ccaa_codigo), False

    lower = plazo_text.lower()
    start_date = (
        base_date + timedelta(days=1)
        if any(k in lower for k in ["siguiente", "següent", "seguinte", "following"])
        else base_date
    )

    # 1. Business days ES/CA/GL/EN ("15 días hábiles", "20 dies hàbils", "15 working/business days")
    m_habiles = re.search(
        r"\b(\d+|un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|doce|quince|veinte|veinticinco|treinta|vint|dez)\s+"
        r"(?:d[ií](?:as|es)\s+(?:h[aáà]bil(?:e?s)?)|working\s+days|business\s+days)",
        lower,
    )
    if m_habiles:
        n = _parse_int_or_word(m_habiles.group(1))
        if n:
            end_date = add_business_days(base_date, n, ccaa_codigo=ccaa_codigo)
            return start_date, end_date, True

    # 2. Calendar days ES/CA/GL/EN ("20 días naturales", "30 dies naturals", "30 calendar days") -> LPACAP 30.5 rollover
    m_naturales = re.search(
        r"\b(\d+|diez|quince|veinte|veinticinco|treinta|trenta)\s+"
        r"(?:d[ií](?:as|es)(?:\s+(?:natural(?:e?s)?))?|calendar\s+days|days)",
        lower,
    )
    if m_naturales:
        n = _parse_int_or_word(m_naturales.group(1))
        if n:
            raw_end = start_date + timedelta(days=n)
            end_date = roll_to_next_business_day(raw_end, ccaa_codigo=ccaa_codigo)
            return start_date, end_date, True

    # 3. Months ES/CA/GL/EN ("un mes", "dos meses", "1 mes", "2 months") -> Fecha a fecha + LPACAP 30.5 rollover
    m_meses = re.search(
        r"\b(\d+|un|uno|una|dos|tres|seis|dues)\s+(?:mes(?:es|os)?|months?)\b",
        lower,
    )
    if m_meses:
        n = _parse_int_or_word(m_meses.group(1))
        if n:
            end_date = add_months_lpacap(base_date, n, ccaa_codigo=ccaa_codigo)
            return start_date, end_date, True

    return None, None, False


def compute_dates_and_status(
    fecha_publicacion: date | str | None = None,
    fecha_inicio_solicitud: date | str | None = None,
    fecha_fin_solicitud: date | str | None = None,
    plazo_texto_original: str | None = None,
    anio_hint: int | None = None,
    ccaa_codigo: str | None = None,
    today: date | None = None,
) -> ResolvedDates:
    """Resolve all dates, status (ACTIVA/PROXIMA/CERRADA) and remaining days."""
    ref_today = today or settings.get_today()
    f_pub = parse_spanish_date(fecha_publicacion)
    f_ini = parse_spanish_date(fecha_inicio_solicitud)
    f_fin = parse_spanish_date(fecha_fin_solicitud)
    es_calculado = False

    anchor_date = f_ini or f_pub
    if anchor_date and not f_fin and plazo_texto_original:
        calc_ini, calc_fin, calc_flag = resolve_deadline_from_text(
            anchor_date,
            plazo_texto_original,
            ccaa_codigo=ccaa_codigo,
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
