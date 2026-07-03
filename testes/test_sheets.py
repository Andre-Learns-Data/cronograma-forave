# ============================================================
# test_sheets.py — Round-trip Google Sheets (sem rede)
# ============================================================
# Verifica que os dados sobrevivem à viagem:
#   gestor -> sincronizar_tudo -> obter_* -> reconstruir
# usando o código REAL de escrita e leitura (com Sheet falso).
# É o que valida que os cabeçalhos das colunas batem certo.
# ============================================================

import unittest

from classes.avaliacao_final import Avaliacao
from classes.carregador_sheets import gestor_a_partir_de_sheets
from classes.formando import Formando
from classes.modulo import Modulo
from gestor_cronograma import GestorCronograma
from testes.fakes import fake_gsheets


class TestRoundTripSheets(unittest.TestCase):

    def setUp(self):
        # Gestor de origem construído à mão (sem gravar em disco)
        self.origem = GestorCronograma(pasta_dados="dados")
        m = Modulo("Programacao Python", "Andre", 50, 30, "em curso",
                   ["01/06/2026", "15/06/2026"], ufcd="5412")
        av0 = Avaliacao("15/06/2026", "projecto", "Projecto", "POO", "Repo", 70)
        av1 = Avaliacao("10/06/2026", "teste", "Teste", "Teoria", "Folha", 30)
        av0.lancar_nota("ana@forave.org", 16)
        av1.lancar_nota("ana@forave.org", 14)
        av0.lancar_nota("rui@forave.org", 10)
        m.avaliacoes = [av0, av1]
        self.origem.modulos = [m]
        self.origem.formandos = [
            Formando("Ana", "ana@forave.org", ["Programacao Python"]),
            Formando("Rui", "rui@forave.org", ["Programacao Python"]),
        ]
        self.origem.professores = []
        self.origem.alteracoes = []
        self.origem.notificacoes = []

        # Sincronizar para o Sheet falso e reconstruir
        gs = fake_gsheets()
        gs.sincronizar_tudo(self.origem)
        self.recon = gestor_a_partir_de_sheets(gs)

    def test_modulo_preservado(self):
        self.assertEqual(len(self.recon.modulos), 1)
        m = self.recon.modulos[0]
        self.assertEqual(m.nome, "Programacao Python")
        self.assertEqual(m.ufcd, "5412")
        self.assertEqual(m.horas_dadas, 30)
        self.assertEqual(m.horas_totais, 50)
        self.assertEqual(m.datas, ["01/06/2026", "15/06/2026"])

    def test_avaliacoes_e_pesos(self):
        avs = self.recon.modulos[0].avaliacoes
        self.assertEqual(len(avs), 2)
        self.assertEqual(avs[0].peso, 70)
        self.assertEqual(avs[1].peso, 30)

    def test_notas_ligadas_corretamente(self):
        m = self.recon.modulos[0]
        self.assertEqual(m.avaliacoes[0].obter_nota("ana@forave.org"), 16)
        self.assertEqual(m.avaliacoes[1].obter_nota("ana@forave.org"), 14)
        self.assertEqual(m.avaliacoes[0].obter_nota("rui@forave.org"), 10)
        self.assertIsNone(m.avaliacoes[1].obter_nota("rui@forave.org"))

    def test_nota_final_identica_apos_roundtrip(self):
        original = self.origem.modulos[0].nota_final("ana@forave.org")
        reconstruida = self.recon.modulos[0].nota_final("ana@forave.org")
        self.assertEqual(original, 15.4)
        self.assertEqual(reconstruida, 15.4)

    def test_formandos_reconstruidos(self):
        self.assertEqual(len(self.recon.formandos), 2)
        self.assertTrue(self.recon.formandos[0].esta_inscrito("Programacao Python"))


class TestAuditoriaSheets(unittest.TestCase):
    """Auditoria append-only na tab 'Auditoria' (código real, Sheet falso)."""

    def test_append_e_leitura_preservam_entradas(self):
        gs = fake_gsheets()
        gs.acrescentar_auditoria("01/07/2026 09:00", "coord@forave.org",
                                 "Lançar notas", "Python, avaliação 0: ana@forave.org=16")
        gs.acrescentar_auditoria("01/07/2026 09:05", "coord@forave.org",
                                 "Adicionar módulo", "Base de Dados (UFCD 0709)")

        registos = gs.obter_auditoria()
        self.assertEqual(len(registos), 2)
        # A ordem de escrita é preservada (append-only)
        self.assertEqual(registos[0]["accao"], "Lançar notas")
        self.assertEqual(registos[0]["autor"], "coord@forave.org")
        self.assertIn("ana@forave.org=16", registos[0]["detalhe"])
        self.assertEqual(registos[1]["accao"], "Adicionar módulo")


if __name__ == "__main__":
    unittest.main()
