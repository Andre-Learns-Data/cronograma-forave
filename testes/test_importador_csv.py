# ============================================================
# test_importador_csv.py — Testes da importação CSV
# ============================================================
# Importação de módulos/formandos/professores, deteção de
# duplicados (saltados), erros de linha e ficheiro inexistente.
# ============================================================

import os
import shutil
import tempfile
import unittest

from classes.importador_csv import ImportadorCSV
from gestor_cronograma import GestorCronograma


class TestImportadorCSV(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.gestor = GestorCronograma(pasta_dados=self.pasta)
        self.imp = ImportadorCSV()

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _escrever(self, nome, conteudo):
        caminho = os.path.join(self.pasta, nome)
        f = open(caminho, "w", encoding="utf-8")
        f.write(conteudo)
        f.close()
        return caminho

    def test_importar_modulos_e_saltar_duplicados(self):
        csv = "nome,professor,horas_totais,horas_dadas,estado\n" \
              "Python,Andre,50,10,em curso\n" \
              "SQL,Marcelo,30,0,pendente\n"
        caminho = self._escrever("modulos.csv", csv)

        r1 = self.imp.importar_modulos(caminho, self.gestor)
        self.assertEqual(r1["importados"], 2)
        self.assertEqual(r1["saltados"], 0)
        self.assertEqual(r1["erros"], 0)

        # Reimportar o mesmo ficheiro -> tudo saltado (duplicados)
        r2 = self.imp.importar_modulos(caminho, self.gestor)
        self.assertEqual(r2["importados"], 0)
        self.assertEqual(r2["saltados"], 2)

    def test_importar_modulos_com_ufcd_opcional(self):
        csv = "ufcd,nome,professor,horas_totais,horas_dadas,estado\n" \
              "5412,Python,Andre,50,10,em curso\n"
        caminho = self._escrever("m.csv", csv)
        self.imp.importar_modulos(caminho, self.gestor)
        self.assertEqual(self.gestor.procurar_modulo("Python").ufcd, "5412")

    def test_importar_modulos_com_datas_opcional(self):
        # A coluna 'datas' (dias de aula separados por ';') carrega o cronograma
        csv = "ufcd,nome,professor,horas_totais,horas_dadas,estado,datas\n" \
              "5412,Python,Andre,50,30,em curso,09/06/2026;16/06/2026;23/06/2026\n"
        caminho = self._escrever("m.csv", csv)
        self.imp.importar_modulos(caminho, self.gestor)
        m = self.gestor.procurar_modulo("Python")
        self.assertEqual(m.datas, ["09/06/2026", "16/06/2026", "23/06/2026"])
        # Última data = fim previsto (usado pela timeline do dashboard)
        self.assertEqual(m.data_fim_prevista(), "23/06/2026")

    def test_importar_modulos_sem_coluna_datas_fica_vazio(self):
        # Sem a coluna 'datas', o módulo entra na mesma (retrocompatível)
        csv = "nome,professor,horas_totais,horas_dadas,estado\n" \
              "SQL,Marcelo,30,0,pendente\n"
        caminho = self._escrever("m.csv", csv)
        self.imp.importar_modulos(caminho, self.gestor)
        self.assertEqual(self.gestor.procurar_modulo("SQL").datas, [])

    def test_importar_modulos_linha_com_erro(self):
        # horas_totais não numérico -> erro nessa linha, a outra entra
        csv = "nome,professor,horas_totais,horas_dadas,estado\n" \
              "Bom,Andre,50,10,em curso\n" \
              "Mau,Andre,xx,10,em curso\n"
        caminho = self._escrever("m.csv", csv)
        r = self.imp.importar_modulos(caminho, self.gestor)
        self.assertEqual(r["importados"], 1)
        self.assertEqual(r["erros"], 1)
        self.assertEqual(len(r["erros_detalhe"]), 1)

    def test_importar_formandos_modulos_por_ponto_e_virgula(self):
        csv = "nome,email,modulos\n" \
              "Ana,ana@x.pt,Python;SQL\n" \
              "Rui,rui@x.pt,\n"
        caminho = self._escrever("f.csv", csv)
        r = self.imp.importar_formandos(caminho, self.gestor)
        self.assertEqual(r["importados"], 2)
        ana = None
        for f in self.gestor.formandos:
            if f.email == "ana@x.pt":
                ana = f
        self.assertEqual(ana.modulos, ["Python", "SQL"])

    def test_importar_formandos_salta_duplicado_por_email(self):
        csv = "nome,email,modulos\nAna,ana@x.pt,Python\n"
        caminho = self._escrever("f.csv", csv)
        self.imp.importar_formandos(caminho, self.gestor)
        r2 = self.imp.importar_formandos(caminho, self.gestor)
        self.assertEqual(r2["saltados"], 1)

    def test_importar_professores(self):
        csv = "nome,email,telefone,modulos\n" \
              "Luis,luis@x.pt,912345678,Python;Redes\n"
        caminho = self._escrever("p.csv", csv)
        r = self.imp.importar_professores(caminho, self.gestor)
        self.assertEqual(r["importados"], 1)
        self.assertTrue(self.gestor.professor_existe("luis@x.pt"))

    def test_ficheiro_inexistente(self):
        r = self.imp.importar_modulos(os.path.join(self.pasta, "nao_existe.csv"), self.gestor)
        self.assertEqual(r["erros"], 1)


if __name__ == "__main__":
    unittest.main()
