# ============================================================
# professor.py — Classe Professor
# ============================================================
# Representa um professor que lecciona módulos no curso.
# Cada professor tem nome, email, telefone e a lista de
# módulos que lecciona.
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários, listas)
# ============================================================


class Professor:
    """
    Representa um professor do curso.

    Atributos:
        nome (str): Nome completo do professor.
        email (str): Email de contacto.
        telefone (str): Número de telefone (string para preservar o 0 inicial).
        modulos (list): Lista de nomes dos módulos que lecciona.
    """

    def __init__(self, nome, email, telefone, modulos):
        """
        Construtor — cria um novo objecto Professor.

        Parâmetros:
            nome (str): Nome completo.
            email (str): Email de contacto.
            telefone (str): Telefone (guardado como string).
            modulos (list): Lista de nomes de módulos.
        """
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.modulos = modulos

    # --------------------------------------------------------
    # Métodos de acção
    # --------------------------------------------------------

    def adicionar_modulo(self, nome_modulo):
        """
        Adiciona um módulo à lista do professor.

        Verifica primeiro se o módulo já existe na lista
        para evitar duplicados.

        Parâmetros:
            nome_modulo (str): Nome do módulo a adicionar.
        """
        # Verificar se já existe — padrão for + if
        ja_existe = False
        for m in self.modulos:
            if m == nome_modulo:
                ja_existe = True

        if ja_existe:
            print(f"  O professor {self.nome} já lecciona {nome_modulo}.")
        else:
            self.modulos.append(nome_modulo)
            print(f"  Módulo {nome_modulo} adicionado ao professor {self.nome}.")

    def remover_modulo(self, nome_modulo):
        """
        Remove um módulo da lista do professor.

        Parâmetros:
            nome_modulo (str): Nome do módulo a remover.
        """
        encontrado = False
        for m in self.modulos:
            if m == nome_modulo:
                encontrado = True

        if encontrado:
            self.modulos.remove(nome_modulo)
            print(f"  Módulo {nome_modulo} removido do professor {self.nome}.")
        else:
            print(f"  O professor {self.nome} não lecciona {nome_modulo}.")

    # --------------------------------------------------------
    # Métodos de apresentação
    # --------------------------------------------------------

    def mostrar_resumo(self):
        """
        Mostra um resumo do professor no terminal.

        Formato:
            Luís Cerejeira | luis.cerejeira@forave.pt | 912345678
            Módulos: Python Avançado, Bases de Dados
        """
        print(f"  {self.nome} | {self.email} | {self.telefone}")

        if len(self.modulos) > 0:
            modulos_texto = ", ".join(self.modulos)
            print(f"  Módulos: {modulos_texto}")
        else:
            print("  Módulos: nenhum módulo atribuído")

        print()

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Professor num dicionário.

        Retorna:
            dict: Dicionário com todos os atributos.
        """
        dados = {}
        dados["nome"] = self.nome
        dados["email"] = self.email
        dados["telefone"] = self.telefone
        dados["modulos"] = self.modulos.copy()

        return dados


def professor_from_dict(dados):
    """
    Cria um objecto Professor a partir de um dicionário.

    Parâmetros:
        dados (dict): Dicionário com as chaves do professor.

    Retorna:
        Professor: Objecto Professor reconstruído.
    """
    professor = Professor(
        nome=dados["nome"],
        email=dados["email"],
        telefone=dados["telefone"],
        modulos=dados["modulos"].copy()
    )

    return professor
