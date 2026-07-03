# ============================================================
# build_exe.ps1 — Cria o executável Windows do terminal (PyInstaller)
# ============================================================
# Correr no PowerShell, a partir da pasta do projecto:
#     .\build_exe.ps1
#
# O que faz:
#   1. garante o PyInstaller instalado (ferramenta de build, não é
#      dependência do programa);
#   2. limpa builds anteriores;
#   3. gera o executável a partir do cronograma.spec.
#
# Resultado: dist\GestorCronograma\GestorCronograma.exe
# Ver INSTRUCOES_EXE.md para o passo-a-passo em linguagem simples.
# ============================================================

Write-Host "==> 1/3  A garantir o PyInstaller..." -ForegroundColor Cyan
python -m pip install --quiet pyinstaller

Write-Host "==> 2/3  A limpar builds anteriores..." -ForegroundColor Cyan
if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist)  { Remove-Item dist  -Recurse -Force }

Write-Host "==> 3/3  A gerar o executavel (pode demorar 1-2 min)..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm cronograma.spec

if (Test-Path "dist\GestorCronograma\GestorCronograma.exe") {
    Write-Host ""
    Write-Host "OK! Executavel criado em:" -ForegroundColor Green
    Write-Host "    dist\GestorCronograma\GestorCronograma.exe" -ForegroundColor Green
    Write-Host "Copia a pasta 'dist\GestorCronograma' toda; corre o .exe la dentro."
} else {
    Write-Host "Falhou: o .exe nao foi criado. Ve as mensagens acima." -ForegroundColor Red
}
