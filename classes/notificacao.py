# ============================================================
# notificacao.py — Classe Notificacao
# ============================================================
# Gere o registo de notificações sobre alterações ao cronograma.
# Oferece dois canais próprios de saída: consola (print) e
# ficheiro (.txt). O envio por email é tratado pelas classes
# EmailSender / BrevoSender (usadas pelo main.py e pelo app.py).
#
# Alinhado com: Aula 5 (POO), Sessão Online 6 (ficheiros)
# ============================================================

from datetime import datetime


class Notificacao:
    """
    Representa uma notificação a enviar.

    Atributos:
        mensagem (str): Texto da notificação (gerado pela Alteracao).
        destinatarios (list): Lista de dicionários com nome e email.
        data_criacao (str): Data e hora de criação (automática).
        enviada (bool): Se a notificação já foi enviada.
    """

    def __init__(self, mensagem, destinatarios):
        """
        Construtor — cria uma nova notificação.

        Parâmetros:
            mensagem (str): Texto a enviar.
            destinatarios (list): Lista de dicts [{"nome": "...", "email": "..."}].
        """
        self.mensagem = mensagem
        self.destinatarios = destinatarios

        agora = datetime.now()
        self.data_criacao = agora.strftime("%d/%m/%Y %H:%M")
        self.enviada = False

    # --------------------------------------------------------
    # Canal 1: Consola — mostra no terminal
    # --------------------------------------------------------

    def enviar_consola(self):
        """
        Mostra a notificação no terminal.

        É o canal mais simples — útil para testes e para
        a demonstração do projecto.
        """
        print()
        print("  " + "=" * 46)
        print("    NOTIFICAÇÃO DE ALTERAÇÃO AO CRONOGRAMA")
        print("  " + "=" * 46)
        print()
        print(f"  Data: {self.data_criacao}")
        print()

        # Mostrar a mensagem linha a linha, com indentação
        linhas = self.mensagem.split("\n")
        for linha in linhas:
            if linha.strip() != "":
                print(f"  {linha}")

        print()
        print(f"  Destinatários ({len(self.destinatarios)}):")

        for d in self.destinatarios:
            print(f"    - {d['nome']} ({d['email']})")

        print()
        print("  " + "=" * 46)
        print()

        self.enviada = True

    # --------------------------------------------------------
    # Canal 2: Ficheiro — grava num ficheiro .txt
    # --------------------------------------------------------

    def enviar_ficheiro(self, caminho):
        """
        Grava a notificação num ficheiro de texto.

        Parâmetros:
            caminho (str): Caminho do ficheiro (ex: "dados/notificacao.txt").

        O ficheiro é aberto em modo "a" (append) para não
        apagar notificações anteriores — cada nova notificação
        é acrescentada no final.

        Conceito: Mesmo padrão do open("w") / open("a") da
        Sessão Online 6, mas aplicado a um caso real.
        """
        try:
            ficheiro = open(caminho, "a", encoding="utf-8")

            ficheiro.write("=" * 50 + "\n")
            ficheiro.write("NOTIFICAÇÃO DE ALTERAÇÃO AO CRONOGRAMA\n")
            ficheiro.write(f"Data: {self.data_criacao}\n")
            ficheiro.write("=" * 50 + "\n\n")
            ficheiro.write(self.mensagem + "\n")
            ficheiro.write(f"Destinatários ({len(self.destinatarios)}):\n")

            for d in self.destinatarios:
                ficheiro.write(f"  - {d['nome']} ({d['email']})\n")

            ficheiro.write("\n" + "-" * 50 + "\n\n")

            ficheiro.close()

            self.enviada = True
            print(f"  Notificação gravada em: {caminho}")

        except FileNotFoundError:
            print(f"  Erro: pasta não encontrada para gravar {caminho}")

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Notificacao num dicionário.

        Retorna:
            dict: Dicionário com todos os atributos.
        """
        dados = {}
        dados["mensagem"] = self.mensagem
        dados["destinatarios"] = []

        # Copiar cada dicionário de destinatário
        for d in self.destinatarios:
            dados["destinatarios"].append(d.copy())

        dados["data_criacao"] = self.data_criacao
        dados["enviada"] = self.enviada

        return dados


def notificacao_from_dict(dados):
    """
    Cria um objecto Notificacao a partir de um dicionário.

    Parâmetros:
        dados (dict): Dicionário com as chaves da notificação.

    Retorna:
        Notificacao: Objecto Notificacao reconstruído.
    """
    # Copiar a lista de destinatários
    destinatarios = []
    for d in dados["destinatarios"]:
        destinatarios.append(d.copy())

    notificacao = Notificacao(
        mensagem=dados["mensagem"],
        destinatarios=destinatarios
    )

    # Restaurar valores do JSON
    notificacao.data_criacao = dados["data_criacao"]
    notificacao.enviada = dados["enviada"]

    return notificacao
