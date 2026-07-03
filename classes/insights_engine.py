# ============================================================
# insights_engine.py — Motor de indicadores (insights)
# ============================================================
# Calcula indicadores a partir dos dados REAIS do sistema
# (os módulos, professores e alterações geridos pelo
# GestorCronograma) para alimentar o dashboard web.
#
# Autoria: base criada pelo Marcelo (dashboard Flask). Evoluída
# no Bloco 3: deixou de usar dados mock e passou a ler do
# GestorCronograma — alinhado com o domínio real do projecto
# (módulos/UFCDs, não um horário com salas). Reescrito no estilo
# do projecto (sem list comprehensions nem lambda — secção 5.1).
#
# Alinhado com: Aula 6 (dicionários, listas, for + if)
# ============================================================


def _por_contagem(par):
    """
    Função-chave para ordenar pares (nome, contagem) pela contagem.

    Recebe um par [nome, contagem] e devolve a contagem. Usada pelo
    sorted() para ordenar do maior para o menor — evita usar lambda
    (convenção do projecto, secção 5.1).
    """
    return par[1]


class InsightsEngine:
    """
    Calcula indicadores a partir dos dados reais do GestorCronograma.

    Atributos:
        gestor (GestorCronograma): A fonte de dados (módulos,
                                   professores, formandos, alterações).
    """

    def __init__(self, gestor):
        """
        Construtor.

        Parâmetros:
            gestor (GestorCronograma): O gestor já com os dados
                                       carregados (carregar_dados()).
        """
        self.gestor = gestor

    def analisar(self):
        """
        Calcula todos os indicadores e devolve-os num dicionário.

        Retorna:
            dict com:
              - professor_workload: lista de [professor, nº módulos]
                                    ordenada do maior para o menor
              - alteracoes_por_modulo: lista de [módulo, nº alterações]
              - estado_modulos: dict {estado: contagem}
              - total_modulos, total_avaliacoes (int)
              - horas_dadas, horas_totais (int)

        Tudo com padrões da Aula 6: lista vazia + for + append,
        contador + for + if, dicionário acumulador.
        """
        gestor = self.gestor

        # --- Carga por professor: nº de módulos de cada professor ---
        # Dicionário acumulador (padrão for + if para inicializar a chave)
        carga = {}
        for m in gestor.modulos:
            if m.professor not in carga:
                carga[m.professor] = 0
            carga[m.professor] = carga[m.professor] + 1

        # Converter o dicionário numa lista de pares e ordenar (desc)
        professor_workload = []
        for nome in carga:
            professor_workload.append([nome, carga[nome]])
        professor_workload = sorted(
            professor_workload, key=_por_contagem, reverse=True
        )

        # --- Alterações por módulo (dados REAIS, já não simulados) ---
        contagem_alteracoes = {}
        for a in gestor.alteracoes:
            if a.modulo_nome not in contagem_alteracoes:
                contagem_alteracoes[a.modulo_nome] = 0
            contagem_alteracoes[a.modulo_nome] = contagem_alteracoes[a.modulo_nome] + 1

        alteracoes_por_modulo = []
        for nome in contagem_alteracoes:
            alteracoes_por_modulo.append([nome, contagem_alteracoes[nome]])
        alteracoes_por_modulo = sorted(
            alteracoes_por_modulo, key=_por_contagem, reverse=True
        )

        # --- Estado dos módulos + totais de horas e avaliações ---
        estado_modulos = {}
        horas_dadas = 0
        horas_totais = 0
        total_avaliacoes = 0
        for m in gestor.modulos:
            if m.estado not in estado_modulos:
                estado_modulos[m.estado] = 0
            estado_modulos[m.estado] = estado_modulos[m.estado] + 1

            horas_dadas = horas_dadas + m.horas_dadas
            horas_totais = horas_totais + m.horas_totais
            total_avaliacoes = total_avaliacoes + len(m.avaliacoes)

        # --- Montar o dicionário de resposta ---
        resultado = {}
        resultado["professor_workload"] = professor_workload
        resultado["alteracoes_por_modulo"] = alteracoes_por_modulo
        resultado["estado_modulos"] = estado_modulos
        resultado["total_modulos"] = len(gestor.modulos)
        resultado["total_avaliacoes"] = total_avaliacoes
        resultado["horas_dadas"] = horas_dadas
        resultado["horas_totais"] = horas_totais

        return resultado
