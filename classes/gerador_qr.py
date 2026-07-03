# ============================================================
# gerador_qr.py — Geração de QR codes
# ============================================================
# Cria um QR code (imagem PNG) que aponta para o endereço da
# página/dashboard. Serve o cenário "wow" do projecto: um
# cartaz com o QR num corredor da escola, ou no slide da
# apresentação — quem aponta a câmara do telemóvel abre logo
# o cronograma (ponte de um meio não-clicável para o telemóvel).
#
# Um QR code é só uma forma visual de guardar um texto (aqui, um
# URL). A câmara do telemóvel lê o desenho e abre o link.
#
# Dependência: qrcode (com Pillow). Instalar: pip install "qrcode[pil]"
# Separação de responsabilidades (5.4): a função devolve o caminho
# do ficheiro criado, sem print() — quem chama decide o que mostrar.
#
# Criado na: Bloco 4 / Fase D (wow factors)
# ============================================================

from io import BytesIO

import qrcode


def gerar_qr_bytes(url):
    """
    Gera um QR code que aponta para um URL e devolve os BYTES do PNG.

    É a variante "para a web": em vez de gravar um ficheiro no disco,
    devolve a imagem em memória, pronta a servir numa resposta HTTP
    (as rotas /modulo/qr.png e /qr-login.png usam isto). Evita escrever
    no disco a cada pedido — importante no alojamento com disco efémero
    (Render) e com vários pedidos ao mesmo tempo.

    Usa exactamente os mesmos parâmetros de qualidade do gerar_qr()
    (fonte única de verdade), documentados nesse.

    Parâmetros:
        url (str): O endereço para onde o QR aponta.

    Retorna:
        bytes: O conteúdo do ficheiro PNG.
    """
    qr = qrcode.QRCode(
        version=None,  # None = ajusta o tamanho automaticamente ao texto
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    imagem = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    return buffer.getvalue()


def gerar_qr(url, caminho="qr_cronograma.png"):
    """
    Gera um QR code que aponta para um URL e grava-o como imagem PNG.

    Parâmetros:
        url (str): O endereço para onde o QR aponta (ex: o URL da
                   dashboard alojada, ou da página pública).
        caminho (str): Onde guardar a imagem. Por defeito
                       "qr_cronograma.png" na pasta actual.

    Retorna:
        str: O caminho do ficheiro PNG criado.

    Detalhes:
        - error_correction MÉDIO (ERROR_CORRECT_M) tolera ~15% de
          danos no código — útil se o cartaz ficar dobrado/sujo.
        - box_size controla o tamanho de cada "quadradinho" (10 px);
          border é a margem branca à volta (4 módulos, o mínimo
          recomendado pela norma do QR).
    """
    qr = qrcode.QRCode(
        version=None,  # None = ajusta o tamanho automaticamente ao texto
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    imagem = qr.make_image(fill_color="black", back_color="white")
    imagem.save(caminho)

    return caminho
