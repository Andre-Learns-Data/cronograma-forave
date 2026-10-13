@echo off
REM ============================================================
REM  Repor o Plano B local a ZERO (apaga a base de dados local).
REM  Ao arrancar a seguir, o site volta a semear o curso limpo.
REM  So mexe no ficheiro LOCAL dados\cronograma.db - nada online.
REM ============================================================
cd /d "%~dp0"
title Repor Plano B local

if exist "dados\cronograma.db" (
  del /q "dados\cronograma.db"
  echo Base de dados local apagada. No proximo arranque, semeia o curso limpo.
) else (
  echo Nao havia base de dados local; ja esta limpo.
)
echo.
pause
