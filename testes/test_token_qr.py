# ============================================================
# test_token_qr.py — Tokens de módulo e QR em memória (Bloco D)
# ============================================================
# Cobre a base do "QR por módulo -> .ics":
#   - criar/validar o token assinado de um módulo (round-trip, expirado,
#     falsificado, chave errada);
#   - gerar o PNG do QR em memória (bytes com assinatura de PNG).
# Não toca na rede nem no disco.
# ============================================================

import unittest

from classes.gerador_qr import gerar_qr_bytes
from classes.token_modulo import criar_token_modulo, validar_token_modulo


class TestTokenModulo(unittest.TestCase):

    SECRET = "chave-de-teste"

    def test_round_trip(self):
        # Um token criado devolve o mesmo nome de módulo ao ser validado.
        token = criar_token_modulo("Python Avançado", self.SECRET)
        self.assertEqual(
            validar_token_modulo(token, self.SECRET), "Python Avançado")

    def test_token_expirado_devolve_none(self):
        # validade_segundos=-1 -> qualquer token já criado tem idade > -1,
        # logo conta como expirado (forma determinística de testar a expiração
        # sem ter de manipular o relógio).
        token = criar_token_modulo("Redes", self.SECRET)
        self.assertIsNone(
            validar_token_modulo(token, self.SECRET, validade_segundos=-1))

    def test_token_falsificado_devolve_none(self):
        # Texto que não é um token assinado -> None (não rebenta).
        self.assertIsNone(validar_token_modulo("lixo-nao-assinado", self.SECRET))

    def test_chave_errada_devolve_none(self):
        # Assinado com uma chave, validado com outra -> assinatura inválida.
        token = criar_token_modulo("Base de Dados", self.SECRET)
        self.assertIsNone(validar_token_modulo(token, "outra-chave"))


class TestGerarQrBytes(unittest.TestCase):

    def test_devolve_png(self):
        dados = gerar_qr_bytes("https://exemplo.pt/login")
        self.assertIsInstance(dados, bytes)
        self.assertTrue(len(dados) > 0)
        # Assinatura de um ficheiro PNG (primeiros 8 bytes).
        self.assertEqual(dados[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
