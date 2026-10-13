@echo off
REM ============================================================
REM  Plano B local - Gestor de Cronograma FORAVE
REM  Faz duplo-clique neste ficheiro para arrancar o site no PC,
REM  sem Internet e sem credenciais Google (base de dados SQLite).
REM  Deixa a janela ABERTA durante a demo; fecha-a para parar.
REM ============================================================
cd /d "%~dp0"
title Plano B - Gestor de Cronograma FORAVE (local)

REM --- Escolhe o Python disponivel no Windows (python ou py) ---
where python >nul 2>nul
if %errorlevel%==0 (set PY=python) else (set PY=py)

REM --- Variaveis para correr offline com SQLite local ---
set FONTE_DADOS=db
set FLASK_SECRET_KEY=plano-b-local-forave

echo === Plano B local - Gestor de Cronograma FORAVE ===
echo.
echo A verificar dependencias...
%PY% -c "import flask, sqlalchemy, qrcode" 2>nul
if errorlevel 1 (
  echo Faltam dependencias - a instalar ^(so na 1a vez, pode demorar 1-2 min^)...
  %PY% -m pip install -r requirements.txt
) else (
  echo Dependencias OK.
)

echo.
echo A arrancar o site em http://127.0.0.1:5000
echo Deixa esta janela ABERTA. Para parar: fecha a janela ou Ctrl+C.
echo Logins: coordenador / professor / aluno  ^|  password: demo1234
echo.

REM --- Abre o browser 4s depois (tempo de o servidor subir) ---
start "abrir browser" /min cmd /c "timeout /t 4 >nul & start http://127.0.0.1:5000"

%PY% app.py

echo.
echo O site parou. Podes fechar esta janela.
pause
