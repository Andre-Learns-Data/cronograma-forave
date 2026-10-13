# ============================================================
# utilizador.py — Classe Utilizador
# ============================================================
# Representa uma conta de acesso à área web autenticada
# (a "área do aluno"). Cada utilizador corresponde a um
# formando que se registou para poder ver as suas notas.
#
# IMPORTANTE: esta classe NÃO guarda a password em texto
# simples — guarda apenas o "hash" (uma impressão digital
# irreversível da password). Quem calcula o hash é o
# GestorAutenticacao (classes/autenticacao.py); aqui só o
# armazenamos. Assim, mesmo que o ficheiro de utilizadores
# seja visto, as passwords não ficam expostas.
#
# Conceitos de POO aplicados (os mesmos das outras classes):
#   - __init__ para inicializar os atributos
#   - to_dict() e from_dict() para converter objecto <-> dicionário
#     (necessário para gravar/ler em JSON)
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários)
# Criada na: Bloco 4 / Nível 2 (login + área do aluno)
# ============================================================


class Utilizador:
    """
    Representa uma conta de acesso à área autenticada.

    Atributos:
        email (str): Email do utilizador (chave única — é o mesmo
                     email do formando na lista de formandos).
        password_hash (str): Hash da password (nunca a password em si).
        papel (str): "aluno" ou "coordenador". Por agora só "aluno".
    """

    def __init__(self, email, password_hash, papel="aluno", confirmado=True):
        """
        Construtor — cria um novo utilizador.

        Parâmetros:
            email (str): Email (chave única).
            password_hash (str): Hash da password (calculado por quem chama).
            papel (str): Papel do utilizador. Por defeito "aluno".
            confirmado (bool): Conta já ativada (email confirmado)? Por defeito
                True — as contas semeadas e todas as que já existiam nascem
                ativas. Só o AUTO-REGISTO (novo) cria contas com confirmado=False,
                que só passam a True quando o aluno abre o link de confirmação
                do email. Fecha o furo de alguém criar conta com o email de
                outra pessoa: sem acesso à caixa de correio, não ativa.
        """
        self.email = email
        self.password_hash = password_hash
        self.papel = papel
        self.confirmado = confirmado

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Utilizador num dicionário.

        Retorna:
            dict: Dicionário com os atributos do utilizador.
        """
        dados = {}
        dados["email"] = self.email
        dados["password_hash"] = self.password_hash
        dados["papel"] = self.papel
        dados["confirmado"] = self.confirmado

        return dados


def utilizador_from_dict(dados):
    """
    Cria um objecto Utilizador a partir de um dicionário.

    É o inverso do to_dict() — recebe um dicionário (vindo do
    JSON) e devolve um objecto Utilizador.

    Parâmetros:
        dados (dict): Dicionário com as chaves do utilizador.

    Retorna:
        Utilizador: Objecto reconstruído.

    Nota: usa .get("papel", "aluno") para retrocompatibilidade —
    contas antigas sem o campo "papel" assumem "aluno". Do mesmo modo,
    .get("confirmado", True) garante que contas criadas ANTES de existir
    a confirmação de email continuam ativas (não se "trancam" sozinhas).
    """
    utilizador = Utilizador(
        email=dados["email"],
        password_hash=dados["password_hash"],
        papel=dados.get("papel", "aluno"),
        confirmado=dados.get("confirmado", True)
    )

    return utilizador
