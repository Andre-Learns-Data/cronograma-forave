# ============================================================
# gerar_demo_docs.py — Gera DEMO.html e DEMO.pdf a partir do DEMO.md
# ============================================================
# Fonte ÚNICA: DEMO.md (Markdown). Este script converte-o para:
#   - DEMO.html  (bonito, com a marca FORAVE e índice clicável)
#   - DEMO.pdf   (portátil/imprimível, com índice)
# Assim há um só sítio para editar (o .md) e os outros dois regeneram-se.
#
# Correr:   python gerar_demo_docs.py
#
# Ferramentas de geração (não são dependências do programa):
#   pip install markdown xhtml2pdf
# ============================================================

import os

import markdown
from xhtml2pdf import pisa

FONTE = "DEMO.md"
SAIDA_HTML = "DEMO.html"
SAIDA_PDF = "DEMO.pdf"

# CSS simples (funciona no browser E no conversor de PDF — sem flexbox/grid).
CSS = """
@page { size: A4; margin: 2cm 1.8cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #2b2b2b;
       line-height: 1.45; max-width: 820px; margin: 24px auto; padding: 0 16px; }
.cabecalho { border-bottom: 3px solid #f7c202; padding-bottom: 8px; margin-bottom: 8px; }
.cabecalho img { height: 34px; }
h1 { color: #0d4a30; font-size: 21pt; }
h2 { color: #196141; font-size: 15pt; border-bottom: 1px solid #dfe5e2;
     padding-bottom: 3px; margin-top: 24px; }
h3 { color: #196141; font-size: 12.5pt; margin-top: 16px; }
a { color: #196141; text-decoration: none; }
code { background: #f2f5f3; padding: 1px 4px; border-radius: 3px;
       font-family: Consolas, monospace; font-size: 10pt; }
pre { background: #f2f5f3; padding: 8px 10px; border-radius: 5px;
      border-left: 3px solid #196141; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th { background: #196141; color: #fff; text-align: left; padding: 5px 8px; font-size: 10pt; }
td { border: 1px solid #dfe5e2; padding: 5px 8px; font-size: 10pt; }
blockquote { background: #fffbe9; border-left: 4px solid #f7c202; margin: 10px 0;
             padding: 8px 12px; color: #5a4b00; }
.toc { background: #f4f7f5; border: 1px solid #dfe5e2; border-left: 4px solid #196141;
       padding: 6px 14px; border-radius: 6px; }
.toc ul { margin: 3px 0; padding-left: 18px; list-style: none; }
.cb { display: inline-block; width: 11px; height: 11px; border: 1.5px solid #196141;
      margin-right: 6px; }
hr { border: none; border-top: 1px solid #e2e8e5; margin: 16px 0; }

/* --- Três registos da demo: passo (lista) · resultado · comentário --- */
/* O passo é o item numerado; a sua acção fica destacada a negrito. */
ol > li { margin-bottom: 6px; }
ol > li > p:first-child { font-weight: bold; color: #1f1f1f; }

/* Caixas de destaque. Sem emojis — o destaque é a cor/caixa (rende no PDF).
   Usam-se classes ÚNICAS (adm-*) e não compostas (.admonition.resultado),
   porque o conversor de PDF (xhtml2pdf) tem suporte fraco a seletores compostos.
   As classes são achatadas em _achatar_caixas() antes da conversão. */
.adm-resultado, .adm-porque, .adm-bastidores, .adm-rgpd {
    margin: 6px 0 10px; padding: 7px 12px 8px; border-radius: 5px; font-size: 10pt; }
.adm-resultado p, .adm-porque p, .adm-bastidores p,
.adm-rgpd p { margin: 0; font-weight: normal; }
.admonition-title { font-weight: bold; font-size: 8.5pt; letter-spacing: .4px;
                    text-transform: uppercase; margin: 0 0 3px; }

/* Resultado esperado — VERDE (o que se deve ver no ecrã). */
.adm-resultado { background: #eef6f1; border-left: 4px solid #196141; color: #274c3c; }
.adm-resultado .admonition-title { color: #0d4a30; }

/* Comentário (porquê / bastidores / rgpd) — AZUL-ARDÓSIA (o "porquê"). */
.adm-porque, .adm-bastidores, .adm-rgpd {
    background: #eef2f8; border-left: 4px solid #3a6ea5; color: #34465c; }
.adm-porque .admonition-title, .adm-bastidores .admonition-title,
.adm-rgpd .admonition-title { color: #274b73; }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="pt"><head><meta charset="utf-8">
<title>Guião de Demonstração — FORAVE</title>
<style>{css}</style></head>
<body>
<div class="cabecalho"><img src="static/forave-logo.png" alt="FORAVE"></div>
{corpo}
</body></html>"""


def _sem_emojis(texto):
    """Remove emojis (o conversor de PDF não tem fonte para eles).

    Mantém setas (→), travessões (—) e o ponto do meio (·).
    """
    saida = []
    for c in texto:
        o = ord(c)
        emoji = (o >= 0x1F000) or (0x2600 <= o <= 0x27BF) or o in (0xFE0F, 0x200D)
        if not emoji:
            saida.append(c)
    return "".join(saida)


def _achatar_caixas(html):
    """Achata `class="admonition tipo"` -> `class="adm-tipo"`.

    O conversor de PDF (xhtml2pdf) não honra seletores CSS compostos
    (`.admonition.resultado`); com uma classe única (`.adm-resultado`) as caixas
    ganham cor/borda tanto no browser como no PDF.
    """
    for tipo in ("resultado", "porque", "bastidores", "rgpd"):
        html = html.replace(f'class="admonition {tipo}"', f'class="adm-{tipo}"')
    return html


def _resolver_caminho(uri, _rel):
    """Resolve caminhos relativos (ex.: static/logo.png) para o disco (PDF)."""
    caminho = os.path.join(os.getcwd(), uri)
    return caminho if os.path.exists(caminho) else uri


def main():
    with open(FONTE, encoding="utf-8") as f:
        md = f.read()

    corpo = markdown.markdown(
        md, extensions=["toc", "tables", "fenced_code", "sane_lists",
                        "admonition"])
    corpo = _achatar_caixas(corpo)

    # HTML (browser): o ☐ vira uma caixinha desenhada por CSS
    html = TEMPLATE.format(css=CSS, corpo=corpo.replace("☐", '<span class="cb"></span>'))
    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  OK  {SAIDA_HTML}")

    # PDF: a fonte base (Helvetica) não tem emojis, a caixinha nem a seta →.
    # Por isso, no PDF: ☐ -> "[ ]", → -> "->", e removem-se os emojis.
    corpo_pdf = corpo.replace("☐", "[ ]&nbsp;")
    html_pdf = _sem_emojis(TEMPLATE.format(css=CSS, corpo=corpo_pdf)).replace("→", "->")
    with open(SAIDA_PDF, "wb") as f:
        estado = pisa.CreatePDF(html_pdf, dest=f, link_callback=_resolver_caminho)
    print(f"  {'OK ' if not estado.err else 'ERRO'} {SAIDA_PDF}")


if __name__ == "__main__":
    main()
