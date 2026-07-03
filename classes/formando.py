# ============================================================
# formando.py — Classe Formando
# ============================================================
# Representa um formando (aluno) inscrito no curso.
# Cada formando tem nome, email e lista de módulos em que
# está inscrito. O email é usado para enviar notificações.
#
# Alinhado com: Aula 5 (POO), Aula 6 (listas, dicionários)
# ============================================================


class Formando:
    """
    Representa um formando/aluno do curso.

    Atributos:
        nome (str): Nome completo do formando.
        email (str): Email para receber notificações.
        modulos (list): Lista de nomes dos módulos em que está inscrito.
    """

    def __init__(self, nome, email, modulos):
        """
        Construtor — cria um novo objecto Formando.

        Parâmetros:
            nome (str): Nome completo.
            email (str): Email de contacto.
            modulos (list): Lista de nomes de módulos inscritos.
        """
        self.nome = nome
        self.email = email
        self.modulos = modulos

    # --------------------------------------------------------
    # Métodos de consulta
    # --------------------------------------------------------

    def esta_inscrito(self, nome_modulo):
        """
        Verifica se o formando está inscrito num módulo.

        Parâmetros:
            nome_modulo (str): Nome do módulo a verificar.

        Retorna:
            bool: True se está inscrito, False se não.

        Conceito: É o padrão for + if com flag variable
        que usámos no S6.Exercicio1.py (pesquisa em ficheiro).
        """
        encontrado = False
        for m in self.modulos:
            if m == nome_modulo:
                encontrado = True

        return encontrado

    # --------------------------------------------------------
    # Métodos de apresentação
    # --------------------------------------------------------

    def mostrar_resumo(self):
        """
        Mostra um resumo do formando no terminal.
        """
        print(f"  {self.nome} | {self.email}")

        if len(self.modulos) > 0:
            modulos_texto = ", ".join(self.modulos)
            print(f"  Inscrito em: {modulos_texto}")
        else:
            print("  Inscrito em: nenhum módulo")

        print()

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Formando num dicionário.

        Retorna:
            dict: Dicionário com todos os atributos.
        """
        dados = {}
        dados["nome"] = self.nome
        dados["email"] = self.email
        dados["modulos"] = self.modulos.copy()

        return dados


def formando_from_dict(dados):
    """
    Cria um objecto Formando a partir de um dicionário.

    Parâmetros:
        dados (dict): Dicionário com as chaves do formando.

    Retorna:
        Formando: Objecto Formando reconstruído.
    """
    formando = Formando(
        nome=dados["nome"],
        email=dados["email"],
        modulos=dados["modulos"].copy()
    )

    return formando
