@echo off
REM ============================================================
REM  Plano B - arranca o Gestor de Cronograma FORAVE no teu PC
REM  (o mesmo site, mas com base de dados LOCAL SQLite, sem
REM   Internet nem credenciais Google). Duplo-clique para correr.
REM ============================================================
cd /d "%~dp0"
chcp 65001 >nul
title Plano B - Gestor de Cronograma FORAVE (local)

echo.
echo ============================================================
echo   Plano B - Gestor de Cronograma FORAVE  (local, offline)
echo ============================================================
echo.

REM --- 1) Bibliotecas: so na 1a vez demora 1-2 min; depois e rapido ---
echo [1/3] A garantir as bibliotecas do projeto (1a vez: 1-2 min)...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
  echo.
  echo [ERRO] O comando "python" nao foi reconhecido, ou a instalacao falhou.
  echo        Confirma que o Python esta instalado e no PATH do Windows.
  echo        (Se usas o WSL/Linux, corre antes: bash _PlanoB_Arrancar.sh)
  echo.
  pause
  exit /b 1
)

REM --- 2) Ambiente: base de dados LOCAL (SQLite) + chave de sessao ---
REM     FONTE_DADOS=db  -> usa dados\cronograma.db (nao o JSON nem o Sheets).
REM     Com a BD vazia, a app semeia sozinha o curso + as 3 contas (demo1234).
set FONTE_DADOS=db
set FLASK_SECRET_KEY=plano-b-local

REM --- 3) Abrir o browser (com um pequeno atraso) e arrancar o servidor ---
echo [2/3] A abrir o browser em http://127.0.0.1:5000 ...
start "" cmd /c "timeout /t 4 >nul & start """" http://127.0.0.1:5000"

echo [3/3] A arrancar o servidor web.
echo.
echo   *** NAO FECHES ESTA JANELA enquanto usas o site. ***
echo   (Para PARAR o site, fecha esta janela.)
echo.
echo   Logins (password de todas: demo1234):
echo     coordenador  chronosforave@gmail.com
echo     professor    luis.cerejeira@forave.pt
echo     aluno        alunoforavecetdados@gmail.com
echo.
python app.py

echo.
echo (O servidor parou.)
pause
