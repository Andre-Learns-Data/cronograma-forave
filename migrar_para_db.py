# ============================================================
# migrar_para_db.py — Migra os dados JSON para a base de dados
# ============================================================
# Lê os ficheiros dados/*.json (o formato antigo) e grava-os na
# base de dados escolhida pela variável DATABASE_URL:
#   - sem DATABASE_URL -> SQLite local (dados/cronograma.db)
#   - postgresql://...  -> PostgreSQL (produção)
#
# Serve para arrancar com dados já existentes. Correr uma vez:
#     python migrar_para_db.py
# ============================================================

import json
import os
import sys

# Garante que o Python encontra o package classes/ quando se corre o script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import classes.repositorio_db as rdb  # noqa: E402

PASTA = os.environ.get("PASTA_DADOS", "dados")


def carregar(nome):
    """Lê um ficheiro dados/<nome>.json; se não existir, devolve lista vazia."""
    caminho = os.path.join(PASTA, nome + ".json")
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as ficheiro:
        return json.load(ficheiro)


def main():
    engine = rdb.criar_engine()   # DATABASE_URL ou SQLite local por defeito
    rdb.criar_tabelas(engine)

    # As 5 entidades do gestor + os utilizadores (tudo de uma vez).
    rdb.guardar_tudo(
        engine,
        carregar("modulos"),
        carregar("professores"),
        carregar("formandos"),
        carregar("alteracoes"),
        carregar("notificacoes"),
        carregar("utilizadores"),
    )

    # Auditoria é append-only: migra entrada a entrada (se houver ficheiro).
    for reg in carregar("auditoria"):
        rdb.registar_auditoria(
            engine,
            reg.get("data_hora", ""),
            reg.get("autor", ""),
            reg.get("accao", ""),
            reg.get("detalhe", ""),
        )

    print("Migração concluída para:", engine.url)


if __name__ == "__main__":
    main()
