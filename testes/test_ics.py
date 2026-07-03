# ============================================================
# test_ics.py — Testes da exportação iCalendar (.ics)
# ============================================================
# Gera o .ics a partir de módulos (com datas) e verifica a estrutura
# RFC 5545: um evento de dia inteiro por data, título/descrição certos,
# datas malformadas ignoradas. Usa um "agora" fixo (determinístico).
# ============================================================

import unittest
from datetime import datetime

from classes.gerador_ics import gerar_ics
from classes.modulo import Modulo


class TestGeradorICS(unittest.TestCase):

    def test_gera_um_evento_por_data(self):
        m = Modulo("Programacao Python", "Andre Moreira", 50, 30, "em curso",
                   ["09/06/2026", "16/06/2026"], ufcd="5412")
        ics = gerar_ics([m], agora=datetime(2026, 7, 1, 10, 0, 0))

        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("END:VCALENDAR", ics)
        self.assertEqual(ics.count("BEGIN:VEVENT"), 2)      # duas datas
        self.assertEqual(ics.count("END:VEVENT"), 2)
        # Evento de dia inteiro: DTEND é o dia seguinte (exclusivo)
        self.assertIn("DTSTART;VALUE=DATE:20260609", ics)
        self.assertIn("DTEND;VALUE=DATE:20260610", ics)
        self.assertIn("SUMMARY:Programacao Python (UFCD 5412)", ics)
        self.assertIn("DESCRIPTION:Professor: Andre Moreira", ics)

    def test_ignora_datas_invalidas(self):
        # 31/02 não existe -> ignorada; só a válida gera evento
        m = Modulo("M", "P", 10, 0, "planeado", ["31/02/2026", "10/10/2026"])
        ics = gerar_ics([m], agora=datetime(2026, 7, 1))
        self.assertEqual(ics.count("BEGIN:VEVENT"), 1)
        self.assertIn("DTSTART;VALUE=DATE:20261010", ics)

    def test_modulo_sem_datas_nao_gera_eventos(self):
        m = Modulo("M", "P", 10, 0, "planeado", [])
        ics = gerar_ics([m], agora=datetime(2026, 7, 1))
        self.assertEqual(ics.count("BEGIN:VEVENT"), 0)
        self.assertIn("BEGIN:VCALENDAR", ics)  # continua um calendário válido

    def test_termina_linhas_em_crlf(self):
        m = Modulo("M", "P", 10, 0, "planeado", ["10/10/2026"])
        ics = gerar_ics([m], agora=datetime(2026, 7, 1))
        self.assertIn("\r\n", ics)  # RFC 5545


if __name__ == "__main__":
    unittest.main()
