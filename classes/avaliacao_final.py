# ============================================================
# avaliacao_final.py — Classe Avaliacao
# ============================================================
# Representa um momento de avaliação de um módulo.
# Um módulo pode ter várias avaliações (avaliação contínua)
# ou apenas uma (avaliação pontual).
#
# O nome do ficheiro é "avaliacao_final" (e não "avaliacao")
# de propósito: evita confusão visual com a classe Alteracao
# no momento do import (Avaliacao vs Alteracao são parecidas).
#
# Conceitos de POO aplicados (os mesmos das outras classes):
#   - __init__ para inicializar os atributos
#   - to_dict() e from_dict() para converter entre objecto e
#     dicionário (necessário para gravar/ler em JSON)
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários)
# Criada na: Sessão 4 / Bloco 2
# ============================================================


class Avaliacao:
    """
    Representa um momento de avaliação de um módulo.

    Atributos:
        data (str): Data da avaliação ("dd/mm/aaaa").
        tipo (str): "pontual", "contínua", "projecto" ou "apresentação".
        descricao (str): Em que consiste a avaliação.
        objectivo (str): O que se pretende avaliar.
        deliverables (str): O que o aluno tem de entregar.
        peso (int ou None): Peso na nota final (0-100). Opcional.
        notas (dict): Notas por aluno {email: nota}, escala 0-20.
    """

    def __init__(self, data, tipo, descricao, objectivo, deliverables, peso=None, notas=None):
        """
        Construtor — cria um novo momento de avaliação.

        Parâmetros:
            data (str): Data da avaliação ("dd/mm/aaaa").
            tipo (str): Tipo de avaliação.
            descricao (str): Descrição do que consiste.
            objectivo (str): Objectivo da avaliação.
            deliverables (str): O que o aluno entrega.
            peso (int): Peso na nota final. Por defeito None
                        (quando o peso ainda não está definido).
            notas (dict): Notas por aluno {email: nota}, escala 0-20.
                          Por defeito None -> {} (sem notas lançadas).

        Evolução (Bloco 3 / Fase notas): Adicionado o atributo notas —
        a classificação de cada aluno neste instrumento de avaliação.
        Opcional (default None -> {}) para retrocompatibilidade com o
        JSON antigo (avaliações sem notas).
        """
        self.data = data
        self.tipo = tipo
        self.descricao = descricao
        self.objectivo = objectivo
        self.deliverables = deliverables
        self.peso = peso

        # Mesma cautela do mutable default das listas: nunca usar {}
        # directamente como valor por defeito do parâmetro.
        if notas is None:
            notas = {}
        self.notas = notas

    # --------------------------------------------------------
    # Métodos de notas (classificações por aluno)
    # --------------------------------------------------------

    def lancar_nota(self, email, nota):
        """
        Lança (ou actualiza) a nota de um aluno neste instrumento.

        Parâmetros:
            email (str): Email do aluno (chave única do formando).
            nota (int ou float): Classificação obtida (escala 0-20).
        """
        self.notas[email] = nota

    def obter_nota(self, email):
        """
        Devolve a nota de um aluno neste instrumento.

        Parâmetros:
            email (str): Email do aluno.

        Retorna:
            A nota, ou None se este aluno ainda não tem nota lançada.
        """
        return self.notas.get(email, None)

    # --------------------------------------------------------
    # Métodos de apresentação
    # --------------------------------------------------------

    def mostrar_resumo(self):
        """
        Mostra um resumo da avaliação no terminal.
        """
        print(f"    [{self.data}] {self.tipo} — {self.descricao}")
        print(f"      Objectivo: {self.objectivo}")
        print(f"      Entrega: {self.deliverables}")

        # O peso é opcional — só mostrar se estiver definido
        if self.peso is not None:
            print(f"      Peso: {self.peso}%")

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Avaliacao num dicionário.

        Retorna:
            dict: Dicionário com todos os atributos da avaliação.
        """
        dados = {}
        dados["data"] = self.data
        dados["tipo"] = self.tipo
        dados["descricao"] = self.descricao
        dados["objectivo"] = self.objectivo
        dados["deliverables"] = self.deliverables
        dados["peso"] = self.peso
        dados["notas"] = self.notas.copy()

        return dados


def avaliacao_from_dict(dados):
    """
    Cria um objecto Avaliacao a partir de um dicionário.

    É o inverso do to_dict() — recebe um dicionário (vindo do
    JSON) e devolve um objecto Avaliacao.

    Parâmetros:
        dados (dict): Dicionário com as chaves da avaliação.

    Retorna:
        Avaliacao: Objecto Avaliacao reconstruído.

    Nota: usa .get("peso", None) porque o peso é opcional —
    avaliações antigas (ou importadas sem peso) não partem o
    programa. Mesmo padrão de retrocompatibilidade usado no
    modulo_from_dict para as avaliações.
    """
    avaliacao = Avaliacao(
        data=dados["data"],
        tipo=dados["tipo"],
        descricao=dados["descricao"],
        objectivo=dados["objectivo"],
        deliverables=dados["deliverables"],
        peso=dados.get("peso", None),
        notas=dados.get("notas", {})
    )

    return avaliacao
