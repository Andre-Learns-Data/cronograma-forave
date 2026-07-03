# ============================================================
# test_dominio.py — Testes das classes de domínio
# ============================================================
# Modulo, Avaliacao e Formando: cálculos, notas, e conversão
# objecto <-> dicionário (round-trip JSON).
# ============================================================

import unittest

from classes.avaliacao_final import Avaliacao, avaliacao_from_dict
from classes.formando import Formando
from classes.modulo import Modulo, modulo_from_dict


class TestModulo(unittest.TestCase):

    def test_horas_restantes(self):
        m = Modulo("M", "P", 50, 20, "em curso", [])
        self.assertEqual(m.horas_restantes(), 30)

    def test_horas_restantes_nunca_negativo(self):
        m = Modulo("M", "P", 50, 80, "em curso", [])
        self.assertEqual(m.horas_restantes(), 0)

    def test_percentagem(self):
        m = Modulo("M", "P", 50, 25, "em curso", [])
        self.assertEqual(m.percentagem_concluida(), 50.0)

    def test_percentagem_divisao_por_zero(self):
        m = Modulo("M", "P", 0, 0, "pendente", [])
        self.assertEqual(m.percentagem_concluida(), 0.0)

    def test_percentagem_limitada_a_100(self):
        m = Modulo("M", "P", 50, 80, "concluido", [])
        self.assertEqual(m.percentagem_concluida(), 100.0)

    def test_esta_concluido(self):
        self.assertTrue(Modulo("M", "P", 50, 50, "x", []).esta_concluido())
        self.assertFalse(Modulo("M", "P", 50, 49, "x", []).esta_concluido())

    def test_data_fim_prevista(self):
        m = Modulo("M", "P", 50, 0, "x", ["01/06/2026", "15/06/2026"])
        self.assertEqual(m.data_fim_prevista(), "15/06/2026")
        self.assertEqual(Modulo("M", "P", 50, 0, "x", []).data_fim_prevista(), "")

    def test_nota_final_ponderada(self):
        m = Modulo("M", "P", 50, 0, "x", [])
        av0 = Avaliacao("d", "t", "d", "o", "e", 70)
        av1 = Avaliacao("d", "t", "d", "o", "e", 30)
        av0.lancar_nota("a@x.pt", 16)
        av1.lancar_nota("a@x.pt", 14)
        m.avaliacoes = [av0, av1]
        # (16*70 + 14*30) / 100 = 15.4
        self.assertEqual(m.nota_final("a@x.pt"), 15.4)

    def test_nota_final_parcial_normaliza_pelos_pesos_lancados(self):
        # Só uma nota lançada: a final é essa nota (peso normalizado)
        m = Modulo("M", "P", 50, 0, "x", [])
        av0 = Avaliacao("d", "t", "d", "o", "e", 70)
        av1 = Avaliacao("d", "t", "d", "o", "e", 30)
        av0.lancar_nota("a@x.pt", 18)
        m.avaliacoes = [av0, av1]
        self.assertEqual(m.nota_final("a@x.pt"), 18.0)

    def test_nota_final_sem_notas_devolve_none(self):
        m = Modulo("M", "P", 50, 0, "x", [])
        m.avaliacoes = [Avaliacao("d", "t", "d", "o", "e", 70)]
        self.assertIsNone(m.nota_final("a@x.pt"))

    def test_roundtrip_dict(self):
        m = Modulo("Python", "Andre", 50, 30, "em curso",
                   ["01/06/2026"], ufcd="5412")
        av = Avaliacao("15/06/2026", "projecto", "Projecto", "POO", "Repo", 70)
        av.lancar_nota("a@x.pt", 17)
        m.avaliacoes = [av]

        m2 = modulo_from_dict(m.to_dict())
        self.assertEqual(m2.nome, "Python")
        self.assertEqual(m2.ufcd, "5412")
        self.assertEqual(m2.datas, ["01/06/2026"])
        self.assertEqual(len(m2.avaliacoes), 1)
        self.assertEqual(m2.avaliacoes[0].obter_nota("a@x.pt"), 17)

    def test_from_dict_retrocompativel(self):
        # JSON antigo: sem 'ufcd' nem 'avaliacoes' não deve rebentar
        dados = {"nome": "X", "professor": "P", "horas_totais": 10,
                 "horas_dadas": 0, "estado": "pendente", "datas": []}
        m = modulo_from_dict(dados)
        self.assertEqual(m.ufcd, "")
        self.assertEqual(m.avaliacoes, [])

    def test_sessoes_sintetizadas_das_datas(self):
        # Um módulo criado só com datas ganha uma sessão por data (0h, por dar).
        m = Modulo("Py", "A", 50, 0, "em curso", ["01/06/2026", "08/06/2026"])
        self.assertEqual([s["data"] for s in m.sessoes],
                         ["01/06/2026", "08/06/2026"])
        self.assertTrue(all(s["horas"] == 0 and not s["realizada"] for s in m.sessoes))

    def test_definir_sessoes_calcula_horas_dadas(self):
        # As horas dadas são a soma das horas das aulas marcadas como "dadas".
        m = Modulo("Py", "A", 50, 0, "em curso", [])
        m.definir_sessoes([
            {"data": "01/06/2026", "horas": 5, "realizada": True},
            {"data": "08/06/2026", "horas": 5, "realizada": True},
            {"data": "15/06/2026", "horas": 5, "realizada": False},
        ])
        self.assertEqual(m.datas, ["01/06/2026", "08/06/2026", "15/06/2026"])
        self.assertEqual(m.horas_dadas, 10)
        self.assertEqual(m.horas_restantes(), 40)

    def test_definir_sessoes_legado_sem_marcar_preserva_horas_dadas(self):
        # Footgun: módulo legado (horas_dadas=30 à mão, sessões só com datas).
        # Guardar o cronograma SEM marcar nada (sessões todas 0h/por dar) NÃO
        # deve apagar as 30h — preserva-se o valor manual.
        m = Modulo("Py", "A", 50, 30, "em curso", ["01/06/2026", "08/06/2026"])
        m.definir_sessoes([
            {"data": "01/06/2026", "horas": 0, "realizada": False},
            {"data": "08/06/2026", "horas": 0, "realizada": False},
        ])
        self.assertEqual(m.horas_dadas, 30)
        self.assertEqual(m.datas, ["01/06/2026", "08/06/2026"])

    def test_definir_sessoes_limpar_modulo_rico_zera(self):
        # Já com informação real (horas/✓), desmarcar tudo baixa as horas dadas
        # — a blindagem só protege o caso legado, não impede o zero intencional.
        m = Modulo("Py", "A", 50, 0, "em curso", [])
        m.definir_sessoes([{"data": "01/06/2026", "horas": 5, "realizada": True}])
        self.assertEqual(m.horas_dadas, 5)
        m.definir_sessoes([{"data": "01/06/2026", "horas": 0, "realizada": False}])
        self.assertEqual(m.horas_dadas, 0)

    def test_roundtrip_sessoes(self):
        # As sessões com informação (horas/realizada) sobrevivem ao to_dict.
        m = Modulo("Py", "A", 50, 0, "em curso", [])
        m.definir_sessoes([{"data": "01/06/2026", "horas": 5, "realizada": True}])
        m2 = modulo_from_dict(m.to_dict())
        self.assertEqual(m2.horas_dadas, 5)
        self.assertEqual(m2.sessoes[0]["realizada"], True)

    def test_roundtrip_preserva_horas_dadas_legado(self):
        # Módulo antigo (horas_dadas escrito à mão, sessões sem informação):
        # o to_dict NÃO deve sobrepor as horas dadas a 0 ao recarregar.
        m = Modulo("Py", "A", 50, 30, "em curso", ["01/06/2026"])
        m2 = modulo_from_dict(m.to_dict())
        self.assertEqual(m2.horas_dadas, 30)
        self.assertEqual(m2.datas, ["01/06/2026"])


class TestAvaliacao(unittest.TestCase):

    def test_lancar_obter_nota(self):
        av = Avaliacao("d", "t", "d", "o", "e", 50)
        self.assertIsNone(av.obter_nota("a@x.pt"))
        av.lancar_nota("a@x.pt", 12)
        self.assertEqual(av.obter_nota("a@x.pt"), 12)

    def test_roundtrip_dict_com_notas_e_peso(self):
        av = Avaliacao("d", "t", "desc", "obj", "ent", 40)
        av.lancar_nota("a@x.pt", 9)
        av2 = avaliacao_from_dict(av.to_dict())
        self.assertEqual(av2.peso, 40)
        self.assertEqual(av2.descricao, "desc")
        self.assertEqual(av2.obter_nota("a@x.pt"), 9)

    def test_roundtrip_peso_none_e_sem_notas(self):
        av = Avaliacao("d", "t", "d", "o", "e")  # peso None
        av2 = avaliacao_from_dict(av.to_dict())
        self.assertIsNone(av2.peso)
        self.assertEqual(av2.notas, {})


class TestFormando(unittest.TestCase):

    def test_esta_inscrito(self):
        f = Formando("Ana", "a@x.pt", ["Python", "SQL"])
        self.assertTrue(f.esta_inscrito("Python"))
        self.assertFalse(f.esta_inscrito("Redes"))


if __name__ == "__main__":
    unittest.main()
