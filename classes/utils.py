# ============================================================
# utils.py — Funções utilitárias para o programa
# ============================================================
# Funções reutilizáveis que não pertencem a nenhuma classe
# específica. Usadas em todo o programa para manter a
# interface do terminal limpa e consistente.
#
# O professor aprovou esta abordagem na Aula 6 — criar
# funções de apoio para cabeçalho, limpar ecrã e pausa.
# ============================================================

import os


def limpar_ecra():
    """
    Limpa o terminal.

    Usa 'cls' no Windows e 'clear' no Linux/Mac.
    O os.name devolve 'nt' se for Windows.
    """
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pausa():
    """
    Pausa o programa até o utilizador carregar em Enter.

    Útil para o utilizador ter tempo de ler o resultado
    antes de o ecrã ser limpo pelo próximo menu.
    """
    input("\nCarrega ENTER para continuar...")


def cabecalho(titulo):
    """
    Mostra um cabeçalho formatado no terminal.

    Parâmetros:
        titulo (str): O texto a mostrar no cabeçalho.

    Exemplo de resultado:
        ============================================
          GESTOR DE CRONOGRAMA — FORAVE
        ============================================
    """
    linha = "=" * 50
    print()
    print(linha)
    print(f"  {titulo}")
    print(linha)
    print()


def pedir_inteiro(mensagem):
    """
    Pede um número inteiro ao utilizador com validação.

    Se o utilizador escrever algo que não é número,
    mostra erro e pede de novo (retry loop).

    Parâmetros:
        mensagem (str): A mensagem a mostrar no input.

    Retorna:
        int: O número inteiro introduzido pelo utilizador.
    """
    while True:
        try:
            valor = int(input(mensagem))
            return valor
        except ValueError:
            print("  Entrada inválida — escreve um número inteiro.")


def pedir_texto(mensagem):
    """
    Pede texto ao utilizador, garantindo que não fica vazio.

    Parâmetros:
        mensagem (str): A mensagem a mostrar no input.

    Retorna:
        str: O texto introduzido (sem espaços extra).
    """
    while True:
        valor = input(mensagem).strip()
        if valor == "":
            print("  Este campo não pode ficar vazio.")
            continue
        return valor


def escolher_da_lista(labels, mensagem="  Escolhe o número: "):
    """
    Mostra uma lista numerada e pede ao utilizador para escolher.

    Parâmetros:
        labels (list): Lista de strings — o texto a mostrar para
                       cada opção. Quem chama prepara os labels
                       a partir dos seus objectos.
        mensagem (str): A mensagem a mostrar no input.

    Retorna:
        int: Índice (0-based) do item escolhido na lista original.
             Devolve -1 se a lista estiver vazia.

    Exemplo de uso:
        labels = []
        for m in gestor.modulos:
            labels.append(m.nome)
        indice = escolher_da_lista(labels, "  Módulo: ")
        if indice >= 0:
            modulo_escolhido = gestor.modulos[indice]

    Evolução (Sessão 3): Função criada para resolver o problema
    identificado na Sessão 2 — ao registar uma alteração, o
    utilizador escreveu "1. Python Avançado" (copiando o número
    da lista mostrada) em vez de apenas "Python Avançado". O
    programa procurava por correspondência exacta de texto e não
    encontrava. Com selecção por número:
      - Elimina erros de digitação (acentos, maiúsculas, espaços)
      - Não há ambiguidade — o programa sabe exactamente qual
        objecto foi escolhido
      - É mais rápido para o utilizador

    Conceitos: while True + try/except ValueError (padrão de
    pedir_inteiro) + validação de intervalo + padrão for + if
    com contador para mostrar a lista numerada.
    """
    # Caso especial: lista vazia — devolve -1 para o chamador decidir
    if len(labels) == 0:
        return -1

    # Mostrar a lista numerada (padrão for + contador da Aula 6)
    contador = 0
    for label in labels:
        contador = contador + 1
        print(f"    {contador}. {label}")
    print()

    # Pedir o número, validar e devolver o índice 0-based
    # Padrão retry loop: while True + try/except + continue
    while True:
        try:
            numero = int(input(mensagem))
        except ValueError:
            print("  Entrada inválida — escreve um número.")
            continue

        # Validar intervalo (1 até tamanho da lista)
        if numero < 1 or numero > len(labels):
            print(f"  Número fora do intervalo (1 a {len(labels)}).")
            continue

        # Converter de 1-based (humano) para 0-based (índice Python)
        return numero - 1
