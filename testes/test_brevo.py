# ============================================================
# test_brevo.py — Testes do envio via Brevo (API HTTP)
# ============================================================
# Testa o BrevoSender SEM tocar na rede: substitui-se o
# urllib...urlopen por um dublê que finge a resposta do Brevo.
# Assim exercita-se o código real (montar o pedido, ler a
# resposta) sem precisar de internet nem de chave verdadeira.
# ============================================================

import json
import unittest
import urllib.error
from unittest.mock import patch

from classes.brevo_sender import BrevoSender


class _FakeResposta:
    """Imita o objecto devolvido por urlopen (com .status e context manager)."""

    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestBrevo(unittest.TestCase):

    def test_nao_configurado_nao_envia(self):
        b = BrevoSender()
        self.assertFalse(b.configurado)
        self.assertFalse(b.enviar("a@forave.org", "A", "Assunto", "Corpo"))

    def test_configurar_activa(self):
        b = BrevoSender()
        b.configurar("CHAVE-123", "remetente@forave.org")
        self.assertTrue(b.configurado)

    def test_envia_constroi_pedido_correcto(self):
        b = BrevoSender()
        b.configurar("CHAVE-123", "remetente@forave.org", "Cronograma FORAVE")

        capturado = {}

        def fake_urlopen(pedido, timeout=None):
            capturado["url"] = pedido.full_url
            capturado["headers"] = pedido.headers
            capturado["body"] = pedido.data
            capturado["metodo"] = pedido.get_method()
            return _FakeResposta(201)

        with patch("classes.brevo_sender.urllib.request.urlopen", fake_urlopen):
            ok = b.enviar("aluno@forave.org", "Aluno", "Repor password", "Corpo do email")

        self.assertTrue(ok)
        self.assertEqual(capturado["url"], "https://api.brevo.com/v3/smtp/email")
        self.assertEqual(capturado["metodo"], "POST")
        # urllib guarda os cabeçalhos com a 1ª letra maiúscula ("Api-key")
        self.assertEqual(capturado["headers"]["Api-key"], "CHAVE-123")
        # O corpo é JSON com remetente, destino, assunto e texto
        dados = json.loads(capturado["body"].decode("utf-8"))
        self.assertEqual(dados["sender"]["email"], "remetente@forave.org")
        self.assertEqual(dados["to"][0]["email"], "aluno@forave.org")
        self.assertEqual(dados["subject"], "Repor password")
        self.assertEqual(dados["textContent"], "Corpo do email")

    def test_reply_to_entra_no_pedido(self):
        # Com reply_to, o pedido leva "replyTo" (o remetente NÃO muda).
        b = BrevoSender()
        b.configurar("CHAVE-123", "chronosforave@gmail.com", "Cronograma FORAVE")
        capturado = {}

        def fake_urlopen(pedido, timeout=None):
            capturado["body"] = pedido.data
            return _FakeResposta(201)

        with patch("classes.brevo_sender.urllib.request.urlopen", fake_urlopen):
            b.enviar("aluno@forave.org", "Aluno", "Assunto", "Corpo",
                     reply_to="luis.cerejeira@forave.pt")

        dados = json.loads(capturado["body"].decode("utf-8"))
        self.assertEqual(dados["replyTo"]["email"], "luis.cerejeira@forave.pt")
        # O remetente mantém-se institucional (só muda o "Responder").
        self.assertEqual(dados["sender"]["email"], "chronosforave@gmail.com")

    def test_sem_reply_to_nao_inclui_campo(self):
        b = BrevoSender()
        b.configurar("CHAVE-123", "chronosforave@gmail.com")
        capturado = {}

        def fake_urlopen(pedido, timeout=None):
            capturado["body"] = pedido.data
            return _FakeResposta(201)

        with patch("classes.brevo_sender.urllib.request.urlopen", fake_urlopen):
            b.enviar("aluno@forave.org", "Aluno", "Assunto", "Corpo")

        dados = json.loads(capturado["body"].decode("utf-8"))
        self.assertNotIn("replyTo", dados)

    def test_erro_http_devolve_false(self):
        b = BrevoSender()
        b.configurar("CHAVE-ERRADA", "remetente@forave.org")

        def fake_urlopen(pedido, timeout=None):
            # 401 = chave inválida; o HTTPError precisa de um corpo legível
            raise urllib.error.HTTPError(
                pedido.full_url, 401, "Unauthorized", {}, _CorpoErro()
            )

        with patch("classes.brevo_sender.urllib.request.urlopen", fake_urlopen):
            self.assertFalse(b.enviar("a@forave.org", "A", "Assunto", "Corpo"))


class _CorpoErro:
    """Imita o ficheiro que o HTTPError lê com .read() (e fecha)."""

    def read(self):
        return b'{"message":"chave invalida"}'

    def close(self):
        pass


if __name__ == "__main__":
    unittest.main()
