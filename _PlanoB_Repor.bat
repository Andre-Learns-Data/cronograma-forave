@echo off
REM ============================================================
REM  Plano B - REPOR a demo a ZERO (curso limpo)
REM  Apaga a base de dados local (dados\cronograma.db) e arranca
REM  de novo; no proximo arranque a app semeia o curso limpo.
REM  A base de dados e UM UNICO ficheiro - apagar e seguro.
REM ============================================================
cd /d "%~dp0"
chcp 65001 >nul
title Plano B - Repor a demo (curso limpo)

echo.
echo === Plano B - repor a demo a ZERO (curso limpo) ===
echo.

if exist "dados\cronograma.db" (
  del /q "dados\cronograma.db"
  echo Base de dados local apagada.
  echo No proximo arranque, a demo e semeada de novo (curso + 3 contas).
) else (
  echo Nao havia base de dados local - ja estava limpo.
)

echo.
echo A arrancar de novo...
echo.
call "%~dp0_PlanoB_Arrancar.bat"
