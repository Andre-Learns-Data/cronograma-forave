#!/usr/bin/env bash
# ============================================================
#  Repor o Plano B local a ZERO (Linux / WSL / macOS).
#  Equivalente ao _PlanoB_Repor.bat: apaga a base de dados
#  local (dados/cronograma.db). Ao arrancar a seguir, o site
#  volta a semear o curso limpo. So mexe no ficheiro LOCAL.
# ============================================================
cd "$(dirname "$0")" || exit 1

if [ -f "dados/cronograma.db" ]; then
  rm -f "dados/cronograma.db"
  echo "Base de dados local apagada. No proximo arranque, semeia o curso limpo."
else
  echo "Nao havia base de dados local; ja esta limpo."
fi
