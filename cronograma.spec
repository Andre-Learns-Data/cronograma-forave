# ============================================================
# cronograma.spec — Empacotamento do terminal como .exe (PyInstaller)
# ============================================================
# Gera um executável Windows do programa de TERMINAL (main.py), para
# quem não tem Python instalado poder usar o Gestor de Cronograma com
# um duplo-clique.
#
# Porquê "onedir" (uma pasta) e não "onefile" (um ficheiro só):
#   o programa LÊ e GRAVA os dados na pasta "dados/" ao lado dele. No
#   modo onefile o conteúdo é extraído para uma pasta temporária que
#   desaparece no fim — perder-se-iam as gravações. No modo onedir o
#   .exe fica numa pasta estável e o "dados/" persiste entre execuções.
#   (A pasta "dados/" é criada sozinha no primeiro arranque.)
#
# Build:   pyinstaller cronograma.spec       (ou correr build_exe.ps1)
# Saída:   dist/GestorCronograma/GestorCronograma.exe   (+ libs na pasta)
#
# Nota: é um ficheiro de configuração do PyInstaller (Python normal). As
# variáveis Analysis/PYZ/EXE/COLLECT são a estrutura que o PyInstaller
# espera. Ver INSTRUCOES_EXE.md para o passo-a-passo simples.
# ============================================================

from PyInstaller.utils.hooks import collect_all

# gspread e google-auth carregam módulos "à socapa" (imports dinâmicos)
# que o PyInstaller não descobre sozinho. O collect_all recolhe tudo o
# que cada pacote precisa. qrcode/PIL entram pelo gerar_qr(). O try/except
# ignora um pacote que não esteja instalado (ex.: google_auth_oauthlib).
datas = []
binaries = []
hiddenimports = []
for _pacote in ("gspread", "google", "google_auth_oauthlib",
                "google_auth_httplib2", "qrcode", "PIL"):
    try:
        _d, _b, _h = collect_all(_pacote)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception:
        pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # O terminal não usa a parte web nem os PDFs — excluir alivia o tamanho.
    excludes=['flask', 'werkzeug', 'jinja2', 'gunicorn', 'reportlab',
              'click', 'itsdangerous'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestorCronograma',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # é um programa de terminal -> mantém a janela
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestorCronograma',
)
