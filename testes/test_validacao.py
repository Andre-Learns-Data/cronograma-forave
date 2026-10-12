# ============================================================
# test_validacao.py — Testes da validação de formato de email
# ============================================================
import unittest

from classes.validacao import email_valido


class TestEmailValido(unittest.TestCase):

    def test_emails_validos(self):
        validos = ["ana@forave.pt", "nome.apelido@forave.org",
                   "x@gmail.com", "  com.espacos.a.volta@x.pt  "]
        for e in validos:
            self.assertTrue(email_valido(e), f"devia ser válido: {e!r}")

    def test_emails_invalidos(self):
        invalidos = [None, "", "   ", "semarroba", "isto-nao-e-email",
                     "a@b", "a@.pt", "a@forave.", "com espaco@x.pt", "dois@@x.pt"]
        for e in invalidos:
            self.assertFalse(email_valido(e), f"devia ser inválido: {e!r}")


if __name__ == "__main__":
    unittest.main()
