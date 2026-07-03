# ============================================================
# modulo.py — Classe Modulo
# ============================================================
# Representa um módulo (disciplina) do cronograma.
# Cada módulo tem um nome, um professor associado, uma carga
# horária total, as horas já dadas, e um estado.
#
# Conceitos de POO aplicados:
#   - __init__ para inicializar os atributos
#   - self para aceder aos atributos do objecto
#   - Métodos que operam sobre os dados do próprio objecto
#   - to_dict() e from_dict() para converter entre objecto e
#     dicionário (necessário para gravar/ler em JSON)
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários)
# ============================================================

# Importar a função que reconstrói avaliações a partir de dicionários.
# É necessária no modulo_from_dict() para restaurar as avaliações
# guardadas no JSON. (avaliacao_final.py não importa modulo.py, por
# isso não há risco de import circular.)
from classes.avaliacao_final import avaliacao_from_dict


def _normalizar_sessao(s):
    """
    Normaliza um dicionário de sessão para a forma canónica.

    Uma sessão é uma aula com data, carga horária e indicação de se já foi
    dada. Isto garante que, venha de onde vier (JSON, Google Sheet, formulário
    web), o dicionário tem sempre as mesmas chaves e os tipos certos.

    Retorna:
        dict: {"data": str, "horas": int|float, "realizada": bool}.
    """
    data = str(s.get("data", "")).strip()
    horas = s.get("horas", 0)
    try:
        horas = float(horas)
    except (TypeError, ValueError):
        horas = 0
    # Mostrar 3 em vez de 3.0 quando não há casas decimais (mais limpo no ecrã).
    if horas == int(horas):
        horas = int(horas)
    return {"data": data, "horas": horas, "realizada": bool(s.get("realizada", False))}


class Modulo:
    """
    Representa um módulo/disciplina do cronograma.

    Atributos:
        ufcd (str): Código oficial da UFCD (ex: "5412"). Opcional ("").
        nome (str): Nome do módulo (ex: "Python Avançado").
        professor (str): Nome do professor responsável.
        horas_totais (int): Carga horária total do módulo.
        horas_dadas (int): Horas já leccionadas.
        estado (str): "em curso", "concluido" ou "pendente".
        datas (list): Lista de datas das sessões (strings "dd/mm/aaaa").
        avaliacoes (list): Lista de objectos Avaliacao do módulo.
    """

    def __init__(self, nome, professor, horas_totais, horas_dadas, estado, datas,
                 avaliacoes=None, ufcd="", sessoes=None):
        """
        Construtor — cria um novo objecto Modulo.

        Parâmetros:
            nome (str): Nome do módulo.
            professor (str): Nome do professor.
            horas_totais (int): Total de horas previstas.
            horas_dadas (int): Horas já leccionadas.
            estado (str): Estado actual do módulo.
            datas (list): Lista de strings com as datas das sessões.
            avaliacoes (list): Lista de objectos Avaliacao. Opcional —
                               por defeito None (módulos criados antes
                               da Sessão 4 não passavam este argumento).
            ufcd (str): Código oficial da UFCD (ex: "5412"). Opcional —
                        por defeito "" (módulos sem código associado).

        Evolução (Sessão 4 / Bloco 2): Adicionado o atributo avaliacoes.
        É opcional (default None) para retrocompatibilidade: o código
        antigo que cria Modulo com 6 argumentos continua a funcionar.

        Evolução (Bloco 2): Adicionado o campo ufcd (código oficial da
        unidade). Opcional (default "") para não partir os calls
        existentes nem o JSON antigo. Por agora é informativo — o nome
        continua a ser a chave de deteção de duplicados.
        """
        self.nome = nome
        self.professor = professor
        self.horas_totais = horas_totais
        self.estado = estado
        self.ufcd = ufcd

        # Sessões (aulas) com data + horas + "realizada".
        #
        # Evolução: cada aula passou a ter carga horária e uma marca de
        # "aula dada". As horas dadas do módulo deixam de ser um número
        # escrito à mão e passam a ser a SOMA das horas das sessões marcadas
        # como realizadas — assim o "30/50h" está sempre certo, sem ninguém
        # ter de o atualizar manualmente.
        #
        # Retrocompatibilidade: os dados antigos só têm a lista `datas`
        # (strings). Se não vierem `sessoes`, criam-se a partir das datas
        # (0h, por dar) e mantém-se o `horas_dadas` que já estava gravado —
        # nada se perde. `self.datas` continua a existir (derivada das
        # sessões) porque muito código a lê (ICS, dashboard, QR, etc.).
        if sessoes:
            self.sessoes = [_normalizar_sessao(s) for s in sessoes
                            if str(s.get("data", "")).strip() != ""]
            self.datas = [s["data"] for s in self.sessoes]
            self.horas_dadas = sum(s["horas"] for s in self.sessoes if s["realizada"])
        else:
            self.datas = datas
            self.horas_dadas = horas_dadas
            self.sessoes = [{"data": d, "horas": 0, "realizada": False} for d in datas]

        # Converter None numa lista nova. NUNCA usar [] directamente como
        # valor por defeito do parâmetro — em Python essa lista seria
        # partilhada por todos os módulos (armadilha do "mutable default").
        if avaliacoes is None:
            avaliacoes = []
        self.avaliacoes = avaliacoes

    # --------------------------------------------------------
    # Métodos de consulta — devolvem informação sobre o módulo
    # --------------------------------------------------------

    def horas_restantes(self):
        """
        Calcula quantas horas faltam para concluir o módulo.

        Retorna:
            int: Horas totais menos horas já dadas.
                 Nunca devolve valor negativo.

        Exemplo:
            Se horas_totais=50 e horas_dadas=25, devolve 25.
        """
        restantes = self.horas_totais - self.horas_dadas

        # Protecção: se por algum motivo as horas dadas
        # ultrapassarem as totais, não devolver negativo
        if restantes < 0:
            restantes = 0

        return restantes

    def percentagem_concluida(self):
        """
        Calcula a percentagem de conclusão do módulo.

        Retorna:
            float: Valor entre 0.0 e 100.0.

        Exemplo:
            Se horas_totais=50 e horas_dadas=25, devolve 50.0.
        """
        # Protecção contra divisão por zero
        if self.horas_totais == 0:
            return 0.0

        percentagem = (self.horas_dadas / self.horas_totais) * 100

        # Limitar a 100% mesmo que horas_dadas > horas_totais
        if percentagem > 100.0:
            percentagem = 100.0

        return percentagem

    def esta_concluido(self):
        """
        Verifica se o módulo já foi totalmente leccionado.

        Retorna:
            bool: True se as horas dadas >= horas totais.
        """
        if self.horas_dadas >= self.horas_totais:
            return True
        else:
            return False

    def data_fim_prevista(self):
        """
        Devolve a última data de sessão do módulo (data de fim prevista).

        Retorna:
            str: A última data da lista de datas, ou "" (string vazia)
                 se o módulo ainda não tiver datas registadas.

        Uso: a página de visualização (dashboard / HTML) usa isto para
        saber até quando o módulo decorre, e a partir daí posicionar
        as avaliações na timeline.
        """
        if len(self.datas) > 0:
            return self.datas[-1]
        else:
            return ""

    def nota_final(self, email):
        """
        Calcula a nota final de um aluno neste módulo (média ponderada).

        Nota final = soma de (nota * peso) dos instrumentos em que o aluno
        TEM nota lançada E que TÊM peso definido, a dividir pela soma desses
        pesos (média ponderada normalizada). Assim funciona mesmo que ainda
        só haja algumas notas lançadas, ou que os pesos não somem 100.

        Parâmetros:
            email (str): Email do aluno (chave única do formando).

        Retorna:
            float: Nota final (0-20) arredondada a 1 casa, ou None se o
                   aluno ainda não tiver notas suficientes para calcular.

        Conceito: padrão acumulador (soma) + for + if (Aula 6).
        (Bloco 3 / Fase notas)
        """
        soma_ponderada = 0
        soma_pesos = 0
        for av in self.avaliacoes:
            nota = av.obter_nota(email)
            # Só conta instrumentos com nota lançada E peso definido
            if nota is not None and av.peso is not None:
                soma_ponderada = soma_ponderada + (nota * av.peso)
                soma_pesos = soma_pesos + av.peso

        if soma_pesos == 0:
            return None

        return round(soma_ponderada / soma_pesos, 1)

    # --------------------------------------------------------
    # Métodos de acção — modificam os dados do módulo
    # --------------------------------------------------------

    def registar_horas(self, horas):
        """
        Regista horas leccionadas adicionais.

        Parâmetros:
            horas (int): Número de horas a adicionar.

        Actualiza o estado para "concluido" se as horas
        totais forem atingidas.
        """
        self.horas_dadas = self.horas_dadas + horas

        # Verificar se o módulo ficou concluído
        if self.esta_concluido():
            self.estado = "concluido"

    def adicionar_data(self, data):
        """
        Adiciona uma nova data de sessão ao módulo.

        Parâmetros:
            data (str): Data no formato "dd/mm/aaaa".

        Mantém `datas` e `sessoes` em sincronia: a nova aula entra sem horas
        e por dar (o professor/coordenador preenche isso depois no editor).
        """
        self.datas.append(data)
        self.sessoes.append({"data": data, "horas": 0, "realizada": False})

    def definir_sessoes(self, sessoes):
        """
        Substitui as sessões (aulas) do módulo pela lista dada.

        Cada sessão é um dicionário {"data", "horas", "realizada"}. Depois de
        as guardar, atualiza automaticamente:
          - `datas` (derivada das sessões, para o resto do código que a lê);
          - `horas_dadas` (soma das horas das sessões marcadas como dadas).

        É este o método que faz a marca de "aula dada" contar para as horas
        dadas e, por consequência, descontar às horas em falta
        (ver horas_restantes()).

        Blindagem (footgun): um módulo LEGADO tem um `horas_dadas` escrito à mão
        e sessões sem informação (só datas, 0h, por dar). Se o editor guardar o
        cronograma desse módulo SEM que se tenham posto horas/✓, chegam sessões
        todas vazias — e recalcular poria `horas_dadas` a 0, apagando o valor
        manual. Por isso só se recalcula quando as sessões que chegam OU as
        atuais trazem informação real; se ambas estiverem vazias, preserva-se
        o `horas_dadas` que já existia.

        Parâmetros:
            sessoes (list): Lista de dicionários de sessão.
        """
        novas = [_normalizar_sessao(s) for s in sessoes
                 if str(s.get("data", "")).strip() != ""]
        novas_tem_info = any(s["horas"] or s["realizada"] for s in novas)
        atuais_tem_info = any(s["horas"] or s["realizada"] for s in self.sessoes)

        self.sessoes = novas
        self.datas = [s["data"] for s in self.sessoes]

        # Só recalcular (e potencialmente zerar) as horas dadas se houver
        # informação real de que partir — senão é um módulo legado guardado
        # "às cegas" e mantemos o valor manual.
        if novas_tem_info or atuais_tem_info:
            self.horas_dadas = sum(s["horas"] for s in self.sessoes if s["realizada"])

    def sessoes_para_persistir(self):
        """
        Devolve as sessões a gravar (JSON/Sheet).

        Se NENHUMA sessão tiver informação real (horas ou marca de "dada"),
        devolve [] — assim os módulos antigos, que só têm datas e um
        `horas_dadas` escrito à mão, não veem as horas dadas sobrepostas a 0
        ao serem recarregados (as sessões sintetizadas têm 0h). As datas
        continuam guardadas na coluna própria, por isso não se perde nada.

        Retorna:
            list: as sessões (cópias) se forem significativas, senão [].
        """
        if any(s["horas"] or s["realizada"] for s in self.sessoes):
            return [dict(s) for s in self.sessoes]
        return []

    def adicionar_avaliacao(self, avaliacao):
        """
        Adiciona um momento de avaliação ao módulo.

        Parâmetros:
            avaliacao (Avaliacao): Objecto Avaliacao a adicionar.

        Mesmo padrão de adicionar_data() — append à lista do módulo.
        Um módulo pode ter várias avaliações (avaliação contínua).
        """
        self.avaliacoes.append(avaliacao)

    # --------------------------------------------------------
    # Métodos de apresentação — mostram informação no terminal
    # --------------------------------------------------------

    def mostrar_resumo(self):
        """
        Mostra um resumo do módulo no terminal.

        Formato:
            Python Avançado | Prof. Luís Cerejeira
            Horas: 25/50 (50.0%) | Estado: em curso
            Próximas datas: 14/05/2026, 21/05/2026
        """
        # Mostrar o código UFCD à frente do nome, se existir
        if self.ufcd != "":
            print(f"  [UFCD {self.ufcd}] {self.nome} | Prof. {self.professor}")
        else:
            print(f"  {self.nome} | Prof. {self.professor}")
        print(f"  Horas: {self.horas_dadas}/{self.horas_totais} "
              f"({self.percentagem_concluida():.1f}%) | "
              f"Estado: {self.estado}")

        if len(self.datas) > 0:
            # Mostrar as datas separadas por vírgula
            datas_texto = ", ".join(self.datas)
            print(f"  Datas: {datas_texto}")
        else:
            print("  Datas: nenhuma data registada")

        # Mostrar as avaliações, se existirem (Sessão 4 / Bloco 2)
        if len(self.avaliacoes) > 0:
            print(f"  Avaliações ({len(self.avaliacoes)}):")
            for av in self.avaliacoes:
                av.mostrar_resumo()

        print()

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Modulo num dicionário.

        Necessário para gravar em JSON — o json.dump() não
        sabe gravar objectos, mas sabe gravar dicionários.

        Retorna:
            dict: Dicionário com todos os atributos do módulo.

        Conceito: É o mesmo padrão do dicionário de estatísticas
        do S6.Exercicio2V2.py — agrupar valores num dicionário
        e devolver com return.
        """
        dados = {}
        dados["ufcd"] = self.ufcd
        dados["nome"] = self.nome
        dados["professor"] = self.professor
        dados["horas_totais"] = self.horas_totais
        dados["horas_dadas"] = self.horas_dadas
        dados["estado"] = self.estado
        dados["datas"] = self.datas.copy()  # .copy() para não partilhar a referência
        # Guardar as sessões (data + horas + realizada). É a fonte "rica";
        # `datas` mantém-se por retrocompatibilidade com quem só lê datas.
        # Só se gravam se tiverem informação real (ver sessoes_para_persistir).
        dados["sessoes"] = self.sessoes_para_persistir()

        # Converter cada avaliação num dicionário (padrão for + append).
        # Não basta .copy(): as avaliações são objectos, e o json.dump()
        # só sabe gravar dicionários — daí chamar o to_dict() de cada uma.
        # (Sessão 4 / Bloco 2)
        lista_avaliacoes = []
        for av in self.avaliacoes:
            lista_avaliacoes.append(av.to_dict())
        dados["avaliacoes"] = lista_avaliacoes

        return dados


def modulo_from_dict(dados):
    """
    Cria um objecto Modulo a partir de um dicionário.

    Esta função é o inverso do to_dict() — recebe um
    dicionário (vindo do JSON) e devolve um objecto Modulo.

    Parâmetros:
        dados (dict): Dicionário com as chaves do módulo.

    Retorna:
        Modulo: Objecto Modulo reconstruído.

    Nota: É uma função normal, não um método da classe,
    porque o objecto ainda não existe quando precisamos
    de a chamar — estamos a criá-lo.
    """
    # Reconstruir as avaliações a partir da lista de dicionários.
    # dados.get("avaliacoes", []) garante retrocompatibilidade: o JSON
    # antigo (anterior à Sessão 4) não tem a chave "avaliacoes" — nesse
    # caso fica uma lista vazia em vez de rebentar com KeyError.
    lista_avaliacoes = []
    for dados_av in dados.get("avaliacoes", []):
        lista_avaliacoes.append(avaliacao_from_dict(dados_av))

    # As sessões só existem no JSON novo. Se não estiverem lá (dados antigos),
    # passa-se None e o construtor cria-as a partir das datas, preservando o
    # horas_dadas que já estava gravado.
    modulo = Modulo(
        nome=dados["nome"],
        professor=dados["professor"],
        horas_totais=dados["horas_totais"],
        horas_dadas=dados["horas_dadas"],
        estado=dados["estado"],
        datas=dados["datas"].copy(),
        avaliacoes=lista_avaliacoes,
        ufcd=dados.get("ufcd", ""),
        sessoes=dados.get("sessoes")
    )

    return modulo
