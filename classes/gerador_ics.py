# ============================================================
# gerador_ics.py — Exportação do cronograma para iCalendar (.ics)
# ============================================================
# Gera um ficheiro de calendário no formato iCalendar (RFC 5545) com
# as aulas dos módulos. O aluno importa o .ics no Google Calendar,
# Outlook ou no calendário do telemóvel e passa a ter as aulas lá,
# com os lembretes nativos do sistema.
#
# É um "canal" de saída a mais, na mesma filosofia multicanal do
# projecto: uma lógica de domínio (os módulos e as suas datas),
# vários formatos de saída (HTML, PDF, QR, e agora .ics).
#
# Só usa a biblioteca padrão (datetime) — sem dependências novas.
# ============================================================

from datetime import datetime, timedelta


def _escapar(texto):
    """
    Escapa um texto para um campo iCalendar (SUMMARY/DESCRIPTION).

    O formato exige escapar \\, ; , e as mudanças de linha (RFC 5545).
    """
    if texto is None:
        texto = ""
    texto = str(texto)
    texto = texto.replace("\\", "\\\\")
    texto = texto.replace(";", "\\;")
    texto = texto.replace(",", "\\,")
    texto = texto.replace("\n", "\\n")
    return texto


def _data_para_datetime(data_ddmmaaaa):
    """Converte 'dd/mm/aaaa' num datetime, ou None se for inválida."""
    try:
        return datetime.strptime(data_ddmmaaaa.strip(), "%d/%m/%Y")
    except (ValueError, AttributeError):
        return None


def gerar_ics(modulos, agora=None):
    """
    Gera o conteúdo iCalendar (.ics) com as aulas dos módulos.

    Cada data de sessão de cada módulo vira um evento de DIA INTEIRO
    (VEVENT com VALUE=DATE), porque o cronograma guarda datas, não horas.

    Parâmetros:
        modulos (list): lista de objectos Modulo (com .nome, .ufcd,
                        .professor e .datas).
        agora (datetime): opcional — usado no DTSTAMP (permite testes
                          determinísticos). Por defeito, datetime.now().

    Retorna:
        str: o ficheiro .ics completo (linhas terminadas em CRLF, RFC 5545).
    """
    if agora is None:
        agora = datetime.now()
    dtstamp = agora.strftime("%Y%m%dT%H%M%SZ")

    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//FORAVE//Cronograma//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for m in modulos:
        titulo = m.nome
        if getattr(m, "ufcd", ""):
            titulo = f"{m.nome} (UFCD {m.ufcd})"
        descricao = f"Professor: {m.professor}" if m.professor else "FORAVE"

        indice = 0
        for data in m.datas:
            dt = _data_para_datetime(data)
            if dt is None:
                continue  # data malformada — ignora (não parte a exportação)
            inicio = dt.strftime("%Y%m%d")
            # Evento de dia inteiro: DTEND é exclusivo -> dia seguinte
            fim = (dt + timedelta(days=1)).strftime("%Y%m%d")
            uid = f"{m.nome}-{inicio}-{indice}@cronograma-forave".replace(" ", "_")
            linhas.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{inicio}",
                f"DTEND;VALUE=DATE:{fim}",
                f"SUMMARY:{_escapar(titulo)}",
                f"DESCRIPTION:{_escapar(descricao)}",
                "END:VEVENT",
            ])
            indice = indice + 1

    linhas.append("END:VCALENDAR")
    return "\r\n".join(linhas) + "\r\n"
