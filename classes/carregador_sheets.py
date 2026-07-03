# ============================================================
# carregador_sheets.py — Reconstruir o gestor a partir do Sheet
# ============================================================
# Quando o dashboard está ALOJADO na internet, não tem a pasta
# dados/ local do coordenador. A fonte de dados passa a ser o
# Google Sheet privado (que o coordenador sincroniza a partir do
# terminal). Este módulo lê as tabs do Sheet e reconstrói um
# objecto GestorCronograma equivalente ao que existiria em local.
#
# Fluxo da informação (Bloco 4):
#   terminal (escreve) -> JSON local -> sincroniza -> Google Sheet
#   -> [este módulo] -> GestorCronograma -> dashboard alojado mostra
#
# Liga as NOTAS às avaliações pela coluna "Indice" (a posição da
# avaliação dentro do módulo) — a mesma ordem usada ao sincronizar.
#
# Conceitos das aulas: dicionários, listas, for + if (Aula 6).
# Criado na: Bloco 4 / Fase B (fonte de dados do dashboard alojado)
# ============================================================

import json

from classes.alteracao import Alteracao
from classes.avaliacao_final import Avaliacao
from classes.formando import Formando
from classes.modulo import Modulo
from classes.professor import Professor
from gestor_cronograma import GestorCronograma


def _para_int(valor, default=0):
    """
    Converte um valor lido do Sheet num inteiro, com segurança.

    O get_all_records() do gspread devolve int quando a célula é
    numérica, mas pode devolver string (ex: "" numa célula vazia).
    Esta função protege contra esses casos (try/except ValueError).

    Parâmetros:
        valor: O valor lido (int, str ou None).
        default (int): Valor a devolver se não der para converter.

    Retorna:
        int: O valor convertido, ou o default.
    """
    if valor is None or valor == "":
        return default
    try:
        return int(valor)
    except ValueError:
        return default


def _sessoes_do_texto(texto):
    """
    Lê a coluna "Sessoes" (JSON) do Sheet e devolve a lista de sessões.

    Devolve None se a coluna estiver vazia ou não existir (dados antigos) —
    nesse caso o Modulo cria as sessões a partir das datas e mantém o
    horas_dadas gravado (retrocompatibilidade).

    Parâmetros:
        texto (str): Conteúdo da célula "Sessoes" (esperado: JSON).

    Retorna:
        list ou None.
    """
    texto = (str(texto) if texto is not None else "").strip()
    if texto == "":
        return None
    try:
        valor = json.loads(texto)
    except (ValueError, TypeError):
        return None
    return valor if isinstance(valor, list) else None


def _texto_para_lista(texto):
    """
    Converte um texto "a, b, c" numa lista ["a", "b", "c"].

    Usado para as datas dos módulos e para os módulos inscritos de
    cada formando, que são guardados no Sheet separados por vírgula.

    Parâmetros:
        texto (str): Texto com itens separados por vírgula.

    Retorna:
        list: Lista de strings sem espaços à volta. Vazia se texto vazio.
    """
    lista = []
    if texto is None:
        return lista
    texto = str(texto).strip()
    if texto == "":
        return lista
    for parte in texto.split(","):
        parte = parte.strip()
        if parte != "":
            lista.append(parte)
    return lista


def gestor_a_partir_de_sheets(gsheets, pasta_dados="dados"):
    """
    Lê as tabs do Google Sheet e devolve um GestorCronograma.

    Reconstrói módulos (com avaliações e notas), formandos e
    alterações — o suficiente para alimentar o dashboard público
    (módulos/insights) e a área autenticada do aluno (notas).

    Parâmetros:
        gsheets (GoogleSheetsSync): ligação JÁ conectada ao Sheet.
        pasta_dados (str): pasta do gestor (só para o __init__; este
                           carregador NÃO grava nada — só lê do Sheet).

    Retorna:
        GestorCronograma: gestor preenchido a partir do Sheet.

    Nota: construímos os objectos e atribuímos directamente às listas
    do gestor (gestor.modulos = ...), sem usar adicionar_*() — assim
    NÃO se dispara guardar_dados() (o alojamento não deve reescrever
    ficheiros a cada leitura).
    """
    gestor = GestorCronograma(pasta_dados=pasta_dados)
    gestor.modulos = []
    gestor.formandos = []
    gestor.professores = []
    gestor.alteracoes = []
    gestor.notificacoes = []

    # --- Módulos ---
    for reg in gsheets.obter_cronograma():
        modulo = Modulo(
            nome=reg.get("Nome", ""),
            professor=reg.get("Professor", ""),
            horas_totais=_para_int(reg.get("Horas Totais", 0)),
            horas_dadas=_para_int(reg.get("Horas Dadas", 0)),
            estado=reg.get("Estado", ""),
            datas=_texto_para_lista(reg.get("Datas", "")),
            ufcd=str(reg.get("UFCD", "")),
            sessoes=_sessoes_do_texto(reg.get("Sessoes", ""))
        )
        gestor.modulos.append(modulo)

    # --- Avaliações (anexadas ao módulo certo, pela ordem da tab) ---
    # A ordem é importante: a coluna "Indice" das notas conta com esta
    # mesma ordem de inserção.
    for reg in gsheets.obter_avaliacoes():
        modulo = gestor.procurar_modulo(reg.get("Módulo", ""))
        if modulo is None:
            continue

        # Peso é opcional — célula vazia significa "sem peso definido"
        peso_bruto = reg.get("Peso", "")
        if peso_bruto is None or peso_bruto == "":
            peso = None
        else:
            peso = _para_int(peso_bruto, default=None)

        avaliacao = Avaliacao(
            data=reg.get("Data", ""),
            tipo=reg.get("Tipo", ""),
            descricao=reg.get("Descrição", ""),
            objectivo=reg.get("Objectivo", ""),
            deliverables=reg.get("Deliverables", ""),
            peso=peso
        )
        modulo.avaliacoes.append(avaliacao)

    # --- Notas (ligadas à avaliação pela coluna "Indice") ---
    for reg in gsheets.obter_notas():
        modulo = gestor.procurar_modulo(reg.get("Módulo", ""))
        if modulo is None:
            continue

        indice = _para_int(reg.get("Indice", -1), default=-1)
        if indice < 0 or indice >= len(modulo.avaliacoes):
            continue

        email = reg.get("Email Aluno", "")
        nota_bruta = reg.get("Nota", "")
        if email == "" or nota_bruta == "" or nota_bruta is None:
            continue

        modulo.avaliacoes[indice].lancar_nota(email, _para_int(nota_bruta))

    # --- Professores (necessário para o papel "professor": permite mapear
    #     o email de quem entra aos módulos que gere). Antes não eram
    #     carregados; passaram a ser para a autorização por papéis funcionar
    #     também no alojamento. ---
    for reg in gsheets.obter_professores():
        professor = Professor(
            nome=reg.get("Nome", ""),
            email=reg.get("Email", ""),
            telefone=str(reg.get("Telefone", "")),
            modulos=_texto_para_lista(reg.get("Módulos", ""))
        )
        gestor.professores.append(professor)

    # --- Formandos ---
    for reg in gsheets.obter_formandos():
        formando = Formando(
            nome=reg.get("Nome", ""),
            email=reg.get("Email", ""),
            modulos=_texto_para_lista(reg.get("Módulos Inscritos", ""))
        )
        gestor.formandos.append(formando)

    # --- Alterações (para o indicador "alterações por módulo") ---
    for reg in gsheets.obter_alteracoes():
        alteracao = Alteracao(
            modulo_nome=reg.get("Módulo", ""),
            data_original=reg.get("Data Original", ""),
            data_nova=reg.get("Nova Data", ""),
            motivo=reg.get("Motivo", ""),
            autor=reg.get("Registado Por", "")
        )
        gestor.alteracoes.append(alteracao)

    return gestor
