# ============================================================
# test_gestor.py — Testes do GestorCronograma
# ============================================================
# CRUD, validações de duplicados, notas, RGPD (remover_formando),
# persistência JSON (round-trip) e registo de alterações.
# Cada teste usa uma pasta temporária — NÃO toca nos dados reais.
# ============================================================

import os
import shutil
import tempfile
import unittest

from gestor_cronograma import GestorCronograma


class TestGestor(unittest.TestCase):

    def setUp(self):
        # Pasta temporária isolada para cada teste
        self.pasta = tempfile.mkdtemp()
        self.gestor = GestorCronograma(pasta_dados=self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_adicionar_devolve_objecto_e_persiste(self):
        m = self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.assertEqual(m.nome, "Python")
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "modulos.json")))

    def test_validacoes_existe(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.gestor.adicionar_professor("Luis", "luis@x.pt", "1", [])
        self.gestor.adicionar_formando("Ana", "ana@x.pt", [])
        self.assertTrue(self.gestor.modulo_existe("Python"))
        self.assertFalse(self.gestor.modulo_existe("SQL"))
        self.assertTrue(self.gestor.professor_existe("luis@x.pt"))
        self.assertTrue(self.gestor.formando_existe("ana@x.pt"))
        self.assertFalse(self.gestor.formando_existe("outro@x.pt"))

    def test_procurar_modulo_inexistente(self):
        self.assertIsNone(self.gestor.procurar_modulo("Nao Existe"))

    def test_editar_modulo_actualiza_campos(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "planeado", [])
        m = self.gestor.editar_modulo(
            "Python", professor="Rita", horas_totais=40, horas_dadas=40,
            estado="concluido", datas=["01/09/2026", "08/09/2026"], ufcd="5412"
        )
        self.assertIsNotNone(m)
        self.assertEqual(m.professor, "Rita")
        self.assertEqual(m.estado, "concluido")
        self.assertEqual(m.horas_totais, 40)
        self.assertEqual(m.datas, ["01/09/2026", "08/09/2026"])
        self.assertEqual(m.ufcd, "5412")
        # Persistiu: um gestor novo relê os mesmos valores
        novo = GestorCronograma(pasta_dados=self.pasta)
        novo.carregar_dados()
        self.assertEqual(novo.procurar_modulo("Python").professor, "Rita")

    def test_editar_modulo_inexistente(self):
        self.assertIsNone(self.gestor.editar_modulo("Nao Existe", professor="X"))

    def test_editar_avaliacao_preserva_notas(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.gestor.adicionar_avaliacao("Python", "d", "t", "Orig", "o", "e", 100)
        self.gestor.lancar_nota("Python", 0, "ana@x.pt", 15)
        av = self.gestor.editar_avaliacao("Python", 0, "d2", "t2", "Nova", "o2", "e2", 80)
        self.assertIsNotNone(av)
        self.assertEqual(av.descricao, "Nova")
        self.assertEqual(av.peso, 80)
        # As notas já lançadas mantêm-se
        self.assertEqual(av.obter_nota("ana@x.pt"), 15)

    def test_remover_avaliacao(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.gestor.adicionar_avaliacao("Python", "d", "t", "A", "o", "e", 50)
        self.gestor.adicionar_avaliacao("Python", "d", "t", "B", "o", "e", 50)
        self.assertTrue(self.gestor.remover_avaliacao("Python", 0))
        avs = self.gestor.procurar_modulo("Python").avaliacoes
        self.assertEqual(len(avs), 1)
        self.assertEqual(avs[0].descricao, "B")  # a "B" subiu para o índice 0

    def test_remover_formando_apaga_tambem_as_notas(self):
        # RGPD: o apagamento tem de ser completo (formando + notas)
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.gestor.adicionar_avaliacao("Python", "d", "t", "x", "o", "e", 100)
        self.gestor.adicionar_formando("Ana", "ana@x.pt", ["Python"])
        self.gestor.lancar_nota("Python", 0, "ana@x.pt", 15)
        self.assertEqual(
            self.gestor.procurar_modulo("Python").avaliacoes[0].obter_nota("ana@x.pt"), 15)
        self.assertTrue(self.gestor.remover_formando("ana@x.pt"))
        self.assertFalse(self.gestor.formando_existe("ana@x.pt"))
        # A nota também desapareceu
        self.assertIsNone(
            self.gestor.procurar_modulo("Python").avaliacoes[0].obter_nota("ana@x.pt"))

    def test_adicionar_avaliacao(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        av = self.gestor.adicionar_avaliacao("Python", "d", "t", "desc", "o", "e", 50)
        self.assertIsNotNone(av)
        self.assertEqual(len(self.gestor.procurar_modulo("Python").avaliacoes), 1)

    def test_adicionar_avaliacao_modulo_inexistente(self):
        self.assertIsNone(
            self.gestor.adicionar_avaliacao("Nao Existe", "d", "t", "x", "o", "e")
        )

    def test_lancar_nota(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.gestor.adicionar_avaliacao("Python", "d", "t", "x", "o", "e", 100)
        ok = self.gestor.lancar_nota("Python", 0, "ana@x.pt", 15)
        self.assertTrue(ok)
        self.assertEqual(self.gestor.procurar_modulo("Python").nota_final("ana@x.pt"), 15.0)

    def test_lancar_nota_indice_invalido(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 10, "em curso", [])
        self.assertFalse(self.gestor.lancar_nota("Python", 5, "a@x.pt", 10))

    def test_lancar_nota_modulo_inexistente(self):
        self.assertFalse(self.gestor.lancar_nota("Nao Existe", 0, "a@x.pt", 10))

    def test_remover_formando(self):
        self.gestor.adicionar_formando("Ana", "ana@x.pt", [])
        self.assertTrue(self.gestor.remover_formando("ana@x.pt"))
        self.assertFalse(self.gestor.formando_existe("ana@x.pt"))
        # Remover de novo -> False (já não existe)
        self.assertFalse(self.gestor.remover_formando("ana@x.pt"))

    def test_persistencia_roundtrip(self):
        self.gestor.adicionar_modulo("Python", "Andre", 50, 30, "em curso",
                                     ["01/06/2026"], ufcd="5412")
        self.gestor.adicionar_avaliacao("Python", "15/06/2026", "projecto",
                                        "Projecto", "POO", "Repo", 70)
        self.gestor.lancar_nota("Python", 0, "ana@x.pt", 16)
        self.gestor.adicionar_formando("Ana", "ana@x.pt", ["Python"])

        # Reler do disco com um gestor novo
        outro = GestorCronograma(pasta_dados=self.pasta)
        outro.carregar_dados()
        self.assertEqual(len(outro.modulos), 1)
        m = outro.procurar_modulo("Python")
        self.assertEqual(m.ufcd, "5412")
        self.assertEqual(m.avaliacoes[0].obter_nota("ana@x.pt"), 16)
        self.assertEqual(len(outro.formandos), 1)

    def test_registar_alteracao_actualiza_data_e_notifica(self):
        self.gestor.adicionar_modulo("Python", "Luis", 50, 10, "em curso",
                                     ["01/06/2026"])
        self.gestor.adicionar_professor("Luis", "luis@x.pt", "1", ["Python"])
        self.gestor.adicionar_formando("Ana", "ana@x.pt", ["Python"])

        notif = self.gestor.registar_alteracao(
            "Python", "01/06/2026", "08/06/2026", "Feriado", "Coord"
        )
        # Data actualizada no módulo
        self.assertIn("08/06/2026", self.gestor.procurar_modulo("Python").datas)
        self.assertNotIn("01/06/2026", self.gestor.procurar_modulo("Python").datas)
        # Notificação criada com destinatários (professor + aluna inscrita)
        self.assertIsNotNone(notif)
        self.assertEqual(len(notif.destinatarios), 2)


if __name__ == "__main__":
    unittest.main()
