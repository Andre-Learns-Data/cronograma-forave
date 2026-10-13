#!/usr/bin/env bash
# ============================================================
#  Plano B - arranca o Gestor de Cronograma FORAVE localmente
#  (Linux / WSL / macOS). Alternativa ao _PlanoB_Arrancar.bat
#  quando o Windows nao reconhece "python".
#  Base de dados LOCAL (SQLite), sem Internet nem credenciais.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo "[1/3] A garantir as bibliotecas (1a vez: 1-2 min)..."
python3 -m pip install -r requirements.txt --quiet || {
  echo "[ERRO] Falhou a instalacao das bibliotecas (python3 no PATH?)."; exit 1; }

# FONTE_DADOS=db -> dados/cronograma.db. Com a BD vazia, a app semeia
# sozinha o curso + as 3 contas (password demo1234) no 1o arranque.
export FONTE_DADOS=db
export FLASK_SECRET_KEY=plano-b-local

echo "[2/3] A abrir o browser em http://127.0.0.1:5000 ..."
( sleep 4; xdg-open http://127.0.0.1:5000 >/dev/null 2>&1 \
    || open http://127.0.0.1:5000 >/dev/null 2>&1 ) &

echo "[3/3] Servidor a arrancar. Ctrl+C para parar."
echo "   Logins (password demo1234): coordenador chronosforave@gmail.com |"
echo "   professor luis.cerejeira@forave.pt | aluno alunoforavecetdados@gmail.com"
python3 app.py
