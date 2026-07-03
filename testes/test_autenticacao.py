# ============================================================
# test_autenticacao.py — Testes do login (JSON e Sheet)
# ============================================================
# Registo, login, duplicados, hash da password, e os dois
# backends: ficheiro JSON local e Google Sheet (com dublê).
# ============================================================

import os
import shutil
import tempfile
import unittest

from classes.autenticacao import GestorAutenticacao
from testes.fakes import fake_gsheets


class TestAuthJSON(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.caminho = os.path.join(self.pasta, "utilizadores.json")
        self.auth = GestorAutenticacao(caminho=self.caminho)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_registar_e_autenticar(self):
        u = self.auth.registar("ana@forave.org", "segredo")
        self.assertIsNotNone(u)
        self.assertTrue(self.auth.email_registado("ana@forave.org"))
        self.assertIsNotNone(self.auth.autenticar("ana@forave.org", "segredo"))

    def test_password_nao_e_guardada_em_texto(self):
        self.auth.registar("ana@forave.org", "segredo")
        conteudo = open(self.caminho, "r", encoding="utf-8").read()
        self.assertNotIn("segredo", conteudo)  # só o hash deve estar no ficheiro

    def test_password_errada_falha(self):
        self.auth.registar("ana@forave.org", "segredo")
        self.assertIsNone(self.auth.autenticar("ana@forave.org", "errada"))

    def test_registo_duplicado_devolve_none(self):
        self.auth.registar("ana@forave.org", "segredo")
        self.assertIsNone(self.auth.registar("ana@forave.org", "outra123"))

    def test_persiste_entre_instancias(self):
        self.auth.registar("ana@forave.org", "segredo")
        outro = GestorAutenticacao(caminho=self.caminho)
        self.assertIsNotNone(outro.autenticar("ana@forave.org", "segredo"))


class TestAuthSheet(unittest.TestCase):
    """Backend Google Sheet (dublê em memória)."""

    def test_registar_no_sheet_e_reler(self):
        gs = fake_gsheets()
        auth = GestorAutenticacao(gsheets=gs)
        self.assertTrue(auth.modo_sheets)

        auth.registar("ana@forave.org", "segredo")
        self.assertTrue(auth.email_registado("ana@forave.org"))

        # Uma instância nova, ligada ao MESMO Sheet, vê a conta criada
        auth2 = GestorAutenticacao(gsheets=gs)
        self.assertIsNotNone(auth2.autenticar("ana@forave.org", "segredo"))
        self.assertIsNone(auth2.autenticar("ana@forave.org", "errada"))

    def test_password_no_sheet_e_hash(self):
        gs = fake_gsheets()
        auth = GestorAutenticacao(gsheets=gs)
        auth.registar("ana@forave.org", "segredo")
        # A tab "Utilizadores" não deve conter a password em texto
        linhas = gs.spreadsheet.tabs["Utilizadores"].get_all_values()
        texto = str(linhas)
        self.assertNotIn("segredo", texto)


class TestReposicaoPassword(unittest.TestCase):
    """Fluxo "esqueci-me da password" — token + redefinição (backend JSON)."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.caminho = os.path.join(self.pasta, "utilizadores.json")
        self.auth = GestorAutenticacao(caminho=self.caminho, secret="chave-de-teste")
        self.auth.registar("ana@forave.org", "segredo")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_token_valido_devolve_email(self):
        token = self.auth.criar_token_reposicao("ana@forave.org")
        self.assertIsNotNone(token)
        self.assertEqual(self.auth.validar_token_reposicao(token), "ana@forave.org")

    def test_token_so_para_email_registado(self):
        # Email sem conta -> não há token a gerar
        self.assertIsNone(self.auth.criar_token_reposicao("estranho@forave.org"))

    def test_token_invalido_e_recusado(self):
        self.assertIsNone(self.auth.validar_token_reposicao("lixo-nao-assinado"))

    def test_token_de_outra_chave_e_recusado(self):
        # Token assinado com OUTRA secret não deve passar nesta auth
        outra = GestorAutenticacao(caminho=self.caminho, secret="chave-diferente")
        token = outra.criar_token_reposicao("ana@forave.org")
        self.assertIsNone(self.auth.validar_token_reposicao(token))

    def test_token_expirado_e_recusado(self):
        token = self.auth.criar_token_reposicao("ana@forave.org")
        # Validade negativa -> qualquer idade do token já a excede (expirado).
        # (Evita ter de esperar/dormir no teste; o itsdangerous compara
        #  idade > validade, por isso -1 garante expiração determinística.)
        self.assertIsNone(self.auth.validar_token_reposicao(token, validade_segundos=-1))

    def test_redefinir_muda_a_password(self):
        self.auth.redefinir_password("ana@forave.org", "nova123")
        self.assertIsNone(self.auth.autenticar("ana@forave.org", "segredo"))
        self.assertIsNotNone(self.auth.autenticar("ana@forave.org", "nova123"))

    def test_token_e_de_uso_unico(self):
        # Depois de mudar a password, o token antigo deixa de ser válido
        token = self.auth.criar_token_reposicao("ana@forave.org")
        self.auth.redefinir_password("ana@forave.org", "nova123")
        self.assertIsNone(self.auth.validar_token_reposicao(token))

    def test_nova_password_persiste_no_ficheiro(self):
        self.auth.redefinir_password("ana@forave.org", "nova123")
        outro = GestorAutenticacao(caminho=self.caminho, secret="chave-de-teste")
        self.assertIsNotNone(outro.autenticar("ana@forave.org", "nova123"))


class TestReposicaoSheet(unittest.TestCase):
    """Reposição de password no backend Google Sheet (dublê em memória)."""

    def test_redefinir_no_sheet_actualiza_hash(self):
        gs = fake_gsheets()
        auth = GestorAutenticacao(gsheets=gs, secret="chave-de-teste")
        auth.registar("ana@forave.org", "segredo")

        auth.redefinir_password("ana@forave.org", "nova123")

        # Instância nova ligada ao MESMO Sheet vê a password actualizada
        auth2 = GestorAutenticacao(gsheets=gs, secret="chave-de-teste")
        self.assertIsNone(auth2.autenticar("ana@forave.org", "segredo"))
        self.assertIsNotNone(auth2.autenticar("ana@forave.org", "nova123"))


if __name__ == "__main__":
    unittest.main()
