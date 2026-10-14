# ============================================================
# main.py — Ponto de entrada do Gestor de Cronograma (TERMINAL)
# ============================================================
# Versão 2: com integração Google Sheets e envio de emails.
#
# O QUE É: este ficheiro é a INTERFACE DE TERMINAL (o menu 1-14,
# S, 0). É UM dos canais da aplicação — o irmão `app.py` é o canal
# WEB. Ambos são cascas finas à volta do MESMO cérebro: a classe
# GestorCronograma (gestor_cronograma.py), que guarda os dados e
# as regras e não sabe nada de terminal, web ou email.
#   "Uma lógica, vários canais": a regra de negócio vive num só
#   sítio; aqui só tratamos de ler input e mostrar resultados.
# Este ficheiro, então: lê o .env, liga as integrações opcionais,
# mostra o menu e, a cada escolha, chama o gestor para fazer o
# trabalho e apresenta o que ele devolve.
#
# O programa funciona SEMPRE, mesmo sem Google Sheets ou email
# configurados. Cada integração extra é um bónus que se activa só
# se as credenciais existirem no .env — por isso o banner do menu
# mostra [Google Sheets: ON/OFF] [Email: ON/OFF] (ON = configurado
# e ligado; OFF = não configurado, mas o programa corre na mesma).
#
# Executar com: python main.py
# ============================================================

import os

from classes.email_sender import EmailSender
from classes.gerador_qr import gerar_qr
from classes.google_sheets import GoogleSheetsSync
from classes.importador_csv import ImportadorCSV
from classes.utils import (
    cabecalho,
    escolher_da_lista,
    limpar_ecra,
    pausa,
    pedir_inteiro,
    pedir_texto,
)
from gestor_cronograma import GestorCronograma


def carregar_configuracao():
    """Lê o .env e devolve dicionário de configurações."""
    config = {
        "email_remetente": "", "email_password": "",
        "email_servidor": "", "email_porta": 587,
        "gsheets_nome": "", "gsheets_credenciais": ""
    }
    try:
        ficheiro = open(".env", "r", encoding="utf-8")
        linhas = ficheiro.readlines()
        ficheiro.close()
        for linha in linhas:
            linha = linha.strip()
            if linha == "" or linha[0] == "#":
                continue
            pos = linha.find("=")
            if pos == -1:
                continue
            chave = linha[:pos].strip()
            valor = linha[pos + 1:].strip()
            if chave == "EMAIL_REMETENTE":
                config["email_remetente"] = valor
            elif chave == "EMAIL_PASSWORD":
                config["email_password"] = valor
            elif chave == "EMAIL_SERVIDOR":
                config["email_servidor"] = valor
            elif chave == "EMAIL_PORTA":
                config["email_porta"] = int(valor)
            elif chave == "GOOGLE_SHEETS_NOME":
                config["gsheets_nome"] = valor
            elif chave == "GOOGLE_SHEETS_CREDENCIAIS":
                config["gsheets_credenciais"] = valor
    except FileNotFoundError:
        pass
    return config


def mostrar_menu(gsheets_activo, email_activo):
    """Mostra o menu principal e o estado das integrações opcionais.

    O banner [Google Sheets: ON/OFF] [Email: ON/OFF] diz, de relance,
    quais os bónus estão activos neste arranque: ON = há credenciais no
    .env e a ligação está de pé; OFF = não configurado — mas o programa
    corre na mesma (as duas integrações são opcionais). Devolve a opção
    que o utilizador escreveu.
    """
    cabecalho("GESTOR DE CRONOGRAMA — FORAVE")
    estado_gs = "ON" if gsheets_activo else "OFF"
    estado_em = "ON" if email_activo else "OFF"
    print(f"  [Google Sheets: {estado_gs}]  [Email: {estado_em}]")
    print()
    print("  1. Ver cronograma (módulos)")
    print("  2. Adicionar módulo")
    print("  3. Ver professores")
    print("  4. Adicionar professor")
    print("  5. Ver formandos")
    print("  6. Adicionar formando")
    print("  7. Registar alteração ao cronograma")
    print("  8. Ver histórico de alterações")
    print("  9. Registar horas leccionadas")
    print("  10. Importar dados CSV (módulos/formandos/professores)")
    print("  11. Adicionar avaliação a um módulo")
    print("  12. Remover formando (RGPD)")
    print("  13. Lançar notas de avaliação")
    print("  14. Gerar QR code da página/dashboard")
    print()
    print("  S. Sincronizar com Google Sheets")
    print("  0. Sair")
    print()
    return input("  Escolhe uma opção: ").strip()


def opcao_ver_cronograma(gestor): # 1 — Ver cronograma (módulos)
    """Opção 1 — Lista os módulos do cronograma (só leitura).

    A listagem em si é feita pelo gestor (gestor.listar_modulos); esta
    camada só limpa o ecrã, põe o cabeçalho e espera por uma tecla.
    """
    limpar_ecra()
    cabecalho("CRONOGRAMA — MÓDULOS")
    gestor.listar_modulos()
    pausa()

def opcao_adicionar_modulo(gestor): # 2 — Adicionar módulo
    """Opção 2 — Cria um módulo novo (pede os campos no terminal).

    Recolhe nome, UFCD (opcional), professor, horas e datas de sessão; o
    estado (pendente/em curso/concluído) é inferido das horas. A escrita
    e a validação de duplicados ficam no gestor — aqui só se pede o input
    e se mostra o resultado.
    """
    limpar_ecra()
    cabecalho("ADICIONAR MÓDULO")
    nome = pedir_texto("  Nome do módulo: ")

    # Evolução (Sessão 3): validar duplicado logo após o input
    # do campo-chave (nome). Evita pedir o resto dos dados se já
    # existe. A lógica está em gestor.modulo_existe() — esta camada
    # (terminal) só decide como apresentar a mensagem ao utilizador.
    if gestor.modulo_existe(nome):
        print(f"\n  Já existe um módulo com o nome '{nome}'.")
        print("  Para evitar duplicados, a operação foi cancelada.")
        pausa()
        return

    # Código UFCD é opcional (Enter para saltar) — Bloco 2.
    # Por agora é informativo; o nome continua a ser a chave de duplicados.
    ufcd = input("  Código UFCD (Enter para saltar): ").strip()

    professor = pedir_texto("  Nome do professor: ")
    horas_totais = pedir_inteiro("  Horas totais: ")
    horas_dadas = pedir_inteiro("  Horas já dadas: ")
    if horas_dadas >= horas_totais:
        estado = "concluido"
    elif horas_dadas > 0:
        estado = "em curso"
    else:
        estado = "pendente"
    datas = []
    print("\n  Datas das sessões (escreve 'fim' para terminar):")
    while True:
        data = input("    Data (dd/mm/aaaa): ").strip()
        if data.lower() == "fim":
            break
        if data == "":
            continue
        datas.append(data)
    modulo = gestor.adicionar_modulo(nome, professor, horas_totais, horas_dadas, estado, datas, ufcd=ufcd)
    # Evolução (Sessão 3): O print é feito aqui (camada terminal) e
    # já não dentro do gestor — permite que a importação CSV, em
    # desenvolvimento por outro elemento do grupo, chame a mesma
    # função em loop sem encher o ecrã.
    print(f"\n  Módulo '{modulo.nome}' adicionado com sucesso.")
    pausa()

def opcao_ver_professores(gestor): # 3 — Ver professores
    """Opção 3 — Lista os professores do curso (só leitura)."""
    limpar_ecra()
    cabecalho("PROFESSORES")
    gestor.listar_professores()
    pausa()

def opcao_adicionar_professor(gestor): # 4 — Adicionar professor
    """Opção 4 — Cria um professor (nome, email, telefone, módulos).

    O email é a chave única (um professor = um email); a validação de
    duplicado é feita pelo gestor, logo após o input do email, para não
    pedir o resto dos dados em vão.
    """
    limpar_ecra()
    cabecalho("ADICIONAR PROFESSOR")
    nome = pedir_texto("  Nome: ")
    email = pedir_texto("  Email: ")

    # Evolução (Sessão 3): validar duplicado pelo email (chave única
    # decidida na Sessão 2 — secção 2.3). Validamos logo após o input
    # do email para não pedir telefone/módulos em vão.
    if gestor.professor_existe(email):
        print(f"\n  Já existe um professor com o email '{email}'.")
        print("  Para evitar duplicados, a operação foi cancelada.")
        pausa()
        return

    telefone = pedir_texto("  Telefone: ")
    modulos = []
    print("\n  Módulos que lecciona (escreve 'fim' para terminar):")
    while True:
        modulo = input("    Módulo: ").strip()
        if modulo.lower() == "fim":
            break
        if modulo == "":
            continue
        modulos.append(modulo)
    professor = gestor.adicionar_professor(nome, email, telefone, modulos)
    # Evolução (Sessão 3): Print na camada terminal — ver
    # docstring de gestor.adicionar_modulo no gestor_cronograma.py.
    print(f"\n  Professor '{professor.nome}' adicionado com sucesso.")
    pausa()

def opcao_ver_formandos(gestor): # 5 — Ver formandos
    """Opção 5 — Lista os formandos (alunos) do curso (só leitura)."""
    limpar_ecra()
    cabecalho("FORMANDOS")
    gestor.listar_formandos()
    pausa()

def opcao_adicionar_formando(gestor): # 6 — Adicionar formando
    """Opção 6 — Inscreve um formando (aluno) no curso.

    Pede nome, email (chave única) e os módulos em que fica inscrito. É a
    mesma validação de duplicado (gestor.formando_existe) que a importação
    CSV reutiliza para decidir se cada linha é um aluno novo.
    """
    limpar_ecra()
    cabecalho("ADICIONAR FORMANDO")
    nome = pedir_texto("  Nome: ")
    email = pedir_texto("  Email: ")

    # Evolução (Sessão 3): validar duplicado pelo email (chave única
    # decidida na Sessão 2 — secção 2.3). Esta mesma função
    # (gestor.formando_existe) será usada pela importação CSV para
    # decidir se cada linha é um formando novo ou actualização.
    if gestor.formando_existe(email):
        print(f"\n  Já existe um formando com o email '{email}'.")
        print("  Para evitar duplicados, a operação foi cancelada.")
        pausa()
        return

    modulos = []
    print("\n  Módulos inscritos (escreve 'fim' para terminar):")
    while True:
        modulo = input("    Módulo: ").strip()
        if modulo.lower() == "fim":
            break
        if modulo == "":
            continue
        modulos.append(modulo)
    formando = gestor.adicionar_formando(nome, email, modulos)
    # Evolução (Sessão 3): Print na camada terminal — ver
    # docstring de gestor.adicionar_modulo no gestor_cronograma.py.
    print(f"\n  Formando '{formando.nome}' adicionado com sucesso.")
    pausa()

def opcao_registar_alteracao(gestor, gsheets, email_sender): # 7 — Regista alteração e notifica por todos os canais
    """Opção 7 — Regista alteração e notifica por todos os canais.

    Evolução (Sessão 3): O nome do módulo passou a ser escolhido
    por número (em vez de input de texto). Resolve o problema
    identificado na Sessão 2, em que o utilizador escreveu
    "1. Python Avançado" copiando o número da lista — o programa
    fazia correspondência exacta de texto e não encontrava o
    módulo. Com selecção numerada, o objecto é obtido directamente
    do índice — sem dependência de digitação correcta.
    """
    limpar_ecra()
    cabecalho("REGISTAR ALTERAÇÃO AO CRONOGRAMA")
    if len(gestor.modulos) == 0:
        print("  Não há módulos registados.")
        pausa()
        return

    # Preparar a lista de nomes (padrão for + append, sem list comp.)
    print("  Módulos disponíveis:")
    labels = []
    for m in gestor.modulos:
        labels.append(m.nome)

    # Selecção por número — devolve índice 0-based
    indice = escolher_da_lista(labels, "  Módulo a alterar (número): ")
    modulo_escolhido = gestor.modulos[indice]
    modulo_nome = modulo_escolhido.nome
    print(f"\n  Módulo seleccionado: {modulo_nome}")

    data_original = pedir_texto("  Data original (dd/mm/aaaa): ")
    data_nova = pedir_texto("  Nova data (dd/mm/aaaa): ")
    motivo = pedir_texto("  Motivo da alteração: ")
    autor = pedir_texto("  Registado por: ")

    notificacao = gestor.registar_alteracao(
        modulo_nome, data_original, data_nova, motivo, autor
    )

    # Sincronizar com Google Sheets
    if gsheets is not None and gsheets.conectado:
        gsheets.sincronizar_tudo(gestor)

    if notificacao is None:
        pausa()
        return

    # Escolher canal de notificação
    print()
    print("  Como enviar a notificação?")
    print("    1. Consola")
    print("    2. Ficheiro")
    print("    3. Email")
    print("    4. Todos os canais")
    print("    5. Não enviar agora")
    print()
    canal = input("  Escolha: ").strip()

    if canal == "1":
        notificacao.enviar_consola()
    elif canal == "2":
        notificacao.enviar_ficheiro("dados/notificacoes.txt")
    elif canal == "3":
        if email_sender.configurado:
            assunto = f"Alteração ao Cronograma — {modulo_nome}"
            email_sender.enviar_para_todos(
                notificacao.destinatarios, assunto, notificacao.mensagem
            )
        else:
            print("\n  Email não configurado. Verifica o .env.")
    elif canal == "4":
        notificacao.enviar_consola()
        notificacao.enviar_ficheiro("dados/notificacoes.txt")
        if email_sender.configurado:
            assunto = f"Alteração ao Cronograma — {modulo_nome}"
            email_sender.enviar_para_todos(
                notificacao.destinatarios, assunto, notificacao.mensagem
            )
    elif canal == "5":
        print("\n  Guardada para envio posterior.")
    else:
        print("\n  Opção inválida.")

    gestor.guardar_dados()
    pausa()

def opcao_ver_alteracoes(gestor): # 8 — Ver histórico de alterações
    """Opção 8 — Mostra o histórico (auditoria) de alterações ao cronograma."""
    limpar_ecra()
    cabecalho("HISTÓRICO DE ALTERAÇÕES")
    gestor.listar_alteracoes()
    pausa()

def opcao_registar_horas(gestor): # 9 — Registar horas leccionadas
    """Opção 9 — Regista horas leccionadas num módulo.

    Evolução (Sessão 3): Selecção do módulo por número em vez de
    texto. Mesma motivação da opção 7 (ver docstring acima) —
    elimina erros de digitação e remove a dependência de
    correspondência exacta de texto. Como bónus, o label inclui
    o progresso de horas (ex: "Python Avançado — 25/50h"), o que
    ajuda o utilizador a identificar o módulo certo de relance.
    """
    limpar_ecra()
    cabecalho("REGISTAR HORAS LECCIONADAS")
    if len(gestor.modulos) == 0:
        print("  Não há módulos registados.")
        pausa()
        return

    # Construir labels com nome + progresso (padrão for + append)
    print("  Módulos:")
    labels = []
    for m in gestor.modulos:
        label = f"{m.nome} — {m.horas_dadas}/{m.horas_totais}h"
        labels.append(label)

    # Selecção por número — devolve directamente o objecto via índice
    indice = escolher_da_lista(labels, "  Módulo (número): ")
    modulo = gestor.modulos[indice]
    print(f"\n  Módulo seleccionado: {modulo.nome}")

    horas = pedir_inteiro("  Horas a registar: ")
    modulo.registar_horas(horas)
    gestor.guardar_dados()
    print(f"\n  {horas}h registadas. Total: {modulo.horas_dadas}/{modulo.horas_totais}h "
          f"({modulo.percentagem_concluida():.1f}%)")
    if modulo.esta_concluido():
        print("  Módulo concluído!")
    pausa()

def opcao_importar_csv(gestor):  # 10 — Importar dados CSV
    """Opção 10 — Importa módulos, formandos ou professores de CSV.

    Evolução (Bloco 2): antes só importava módulos e o ImportadorCSV
    imprimia o resultado. Agora pergunta o tipo de dados, o importador
    DEVOLVE um resumo (separação de responsabilidades, secção 5.4) e é
    esta camada (terminal) que o apresenta. Duplicados são saltados.
    """
    limpar_ecra()
    cabecalho("IMPORTAR DADOS DE CSV")

    print("  O que queres importar?")
    print("    1. Módulos       (cabeçalho: nome,professor,horas_totais,horas_dadas,estado)")
    print("    2. Formandos     (cabeçalho: nome,email,modulos)")
    print("    3. Professores   (cabeçalho: nome,email,telefone,modulos)")
    print("  (a coluna 'modulos' usa ';' para separar — ex: Python;SQL)")
    print()
    tipo = input("  Escolha: ").strip()

    if tipo != "1" and tipo != "2" and tipo != "3":
        print("\n  Opção inválida.")
        pausa()
        return

    caminho = pedir_texto("  Caminho do ficheiro CSV: ")

    importador = ImportadorCSV()
    if tipo == "1":
        resumo = importador.importar_modulos(caminho, gestor)
    elif tipo == "2":
        resumo = importador.importar_formandos(caminho, gestor)
    else:
        resumo = importador.importar_professores(caminho, gestor)

    # Apresentar o resumo (o importador só devolve dados, não imprime)
    print()
    print(f"  Importados: {resumo['importados']}")
    print(f"  Saltados (duplicados): {resumo['saltados']}")
    print(f"  Erros: {resumo['erros']}")
    if len(resumo["erros_detalhe"]) > 0:
        print("\n  Detalhe dos erros:")
        for msg in resumo["erros_detalhe"]:
            print(f"    - {msg}")

    pausa()

def opcao_adicionar_avaliacao(gestor):  # 11 — Adicionar avaliação a um módulo
    """Opção 11 — Adiciona um momento de avaliação a um módulo.

    Selecção do módulo por número (mesmo padrão das opções 7 e 9).
    O peso é opcional: Enter em branco deixa-o por definir.
    (Sessão 4 / Bloco 2)
    """
    limpar_ecra()
    cabecalho("ADICIONAR AVALIAÇÃO A UM MÓDULO")
    if len(gestor.modulos) == 0:
        print("  Não há módulos registados.")
        pausa()
        return

    # Escolher o módulo por número (padrão for + append + escolher_da_lista)
    print("  Módulos disponíveis:")
    labels = []
    for m in gestor.modulos:
        labels.append(m.nome)
    indice = escolher_da_lista(labels, "  Módulo a avaliar (número): ")
    modulo = gestor.modulos[indice]
    print(f"\n  Módulo seleccionado: {modulo.nome}")

    # Recolher os dados da avaliação
    data = pedir_texto("  Data da avaliação (dd/mm/aaaa): ")
    tipo = pedir_texto("  Tipo (pontual/contínua/projecto/apresentação): ")
    descricao = pedir_texto("  Descrição (em que consiste): ")
    objectivo = pedir_texto("  Objectivo (o que se avalia): ")
    deliverables = pedir_texto("  Entregáveis (o que o aluno entrega): ")

    # Peso é opcional — Enter em branco = sem peso definido
    peso_texto = input("  Peso na nota final 0-100 (Enter para saltar): ").strip()
    if peso_texto == "":
        peso = None
    else:
        try:
            peso = int(peso_texto)
        except ValueError:
            print("  Peso inválido — fica sem peso definido.")
            peso = None

    avaliacao = gestor.adicionar_avaliacao(
        modulo.nome, data, tipo, descricao, objectivo, deliverables, peso
    )
    if avaliacao is None:
        print("\n  Não foi possível adicionar (módulo não encontrado).")
    else:
        print(f"\n  Avaliação adicionada ao módulo '{modulo.nome}'.")
    pausa()

def opcao_remover_formando(gestor):  # 12 — Remover formando (RGPD)
    """Opção 12 — Remove um formando e elimina os seus dados (RGPD).

    Selecção por número + confirmação explícita (a remoção é
    irreversível). Concretiza o direito ao apagamento (secção 6).
    (Sessão 4 / Bloco 2)
    """
    limpar_ecra()
    cabecalho("REMOVER FORMANDO (RGPD)")
    if len(gestor.formandos) == 0:
        print("  Não há formandos registados.")
        pausa()
        return

    # Escolher o formando por número; label com nome + email
    print("  Formandos registados:")
    labels = []
    for f in gestor.formandos:
        labels.append(f"{f.nome} — {f.email}")
    indice = escolher_da_lista(labels, "  Formando a remover (número): ")
    formando = gestor.formandos[indice]

    # Confirmação explícita — a remoção é irreversível
    print(f"\n  Vais remover: {formando.nome} ({formando.email})")
    confirmacao = input("  Tens a certeza? (s/n): ").strip().lower()
    if confirmacao != "s":
        print("\n  Remoção cancelada.")
        pausa()
        return

    removido = gestor.remover_formando(formando.email)
    if removido:
        print("\n  Formando removido. Os seus dados foram eliminados (RGPD).")
    else:
        print("\n  Não foi encontrado nenhum formando com esse email.")
    pausa()

def opcao_lancar_notas(gestor):  # 13 — Lançar notas de avaliação
    """Opção 13 — Lança as notas (0-20) de um instrumento de avaliação.

    Fluxo: escolher módulo -> escolher avaliação -> introduzir a nota de
    cada formando inscrito no módulo (Enter em branco salta). Coerente
    com a filosofia "o terminal escreve, a web mostra" (Bloco 3).
    A nota final da UFCD é calculada automaticamente a partir dos pesos.
    """
    limpar_ecra()
    cabecalho("LANÇAR NOTAS DE AVALIAÇÃO")
    if len(gestor.modulos) == 0:
        print("  Não há módulos registados.")
        pausa()
        return

    # 1) Escolher o módulo (padrão for + append + escolher_da_lista)
    print("  Módulos disponíveis:")
    labels = []
    for m in gestor.modulos:
        labels.append(m.nome)
    indice_m = escolher_da_lista(labels, "  Módulo (número): ")
    modulo = gestor.modulos[indice_m]

    # 2) Escolher a avaliação (instrumento) do módulo
    if len(modulo.avaliacoes) == 0:
        print(f"\n  O módulo '{modulo.nome}' ainda não tem avaliações.")
        print("  Cria uma primeiro na opção 11.")
        pausa()
        return

    print(f"\n  Avaliações de '{modulo.nome}':")
    labels_av = []
    for av in modulo.avaliacoes:
        if av.peso is None:
            peso_txt = ""
        else:
            peso_txt = f" (peso {av.peso}%)"
        labels_av.append(f"{av.data} — {av.tipo}: {av.descricao}{peso_txt}")
    indice_av = escolher_da_lista(labels_av, "  Avaliação (número): ")
    avaliacao = modulo.avaliacoes[indice_av]

    # 3) Formandos inscritos neste módulo (padrão for + if)
    inscritos = []
    for f in gestor.formandos:
        if f.esta_inscrito(modulo.nome):
            inscritos.append(f)

    if len(inscritos) == 0:
        print(f"\n  Não há formandos inscritos em '{modulo.nome}'.")
        pausa()
        return

    # 4) Lançar a nota de cada inscrito (0-20). Enter em branco salta.
    print("\n  Notas de 0 a 20. Enter em branco salta o aluno.\n")
    contador = 0
    for f in inscritos:
        # Mostrar a nota actual, se já existir, para facilitar a correcção
        nota_actual = avaliacao.obter_nota(f.email)
        if nota_actual is None:
            sufixo = ""
        else:
            sufixo = f" [actual: {nota_actual}]"

        texto = input(f"    {f.nome}{sufixo}: ").strip()
        if texto == "":
            continue

        try:
            nota = int(texto)
        except ValueError:
            print("      Nota inválida — saltado.")
            continue

        if nota < 0 or nota > 20:
            print("      Fora do intervalo 0-20 — saltado.")
            continue

        gestor.lancar_nota(modulo.nome, indice_av, f.email, nota)
        contador = contador + 1

    # 5) Mostrar um resumo: notas finais da UFCD dos inscritos
    print(f"\n  {contador} nota(s) lançada(s).")
    print("\n  Notas finais (UFCD) até ao momento:")
    for f in inscritos:
        final = modulo.nota_final(f.email)
        if final is None:
            print(f"    {f.nome}: ainda sem nota final")
        else:
            print(f"    {f.nome}: {final}")
    pausa()

def opcao_gerar_qr(gestor):  # 14 — Gerar QR code da página/dashboard
    """Opção 14 — Gera um QR code que aponta para a página/dashboard.

    O QR é um artefacto físico (cartaz, slide): quem aponta a câmara
    do telemóvel abre logo o cronograma. Pede o URL (sugere um valor)
    e grava o PNG. A lógica vive em classes/gerador_qr.py (devolve o
    caminho, sem print — separação de responsabilidades, secção 5.4).
    (Bloco 4 / Fase D — wow factors)
    """
    limpar_ecra()
    cabecalho("GERAR QR CODE")
    print("  O QR vai apontar para o endereço da página/dashboard.")
    print("  Enquanto não estiver alojada, podes usar o endereço local")
    print("  (ex: http://127.0.0.1:5000) só para testar.")
    print()
    url = input("  URL (Enter para http://127.0.0.1:5000): ").strip()
    if url == "":
        url = "http://127.0.0.1:5000"

    caminho = input("  Nome do ficheiro (Enter para qr_cronograma.png): ").strip()
    if caminho == "":
        caminho = "qr_cronograma.png"

    try:
        ficheiro = gerar_qr(url, caminho)
        print(f"\n  QR code criado: {ficheiro}")
        print(f"  Aponta para: {url}")
    except Exception as erro:
        print(f"\n  Não foi possível gerar o QR: {erro}")
    pausa()

def opcao_sincronizar(gestor, gsheets): # S — Sincronizar com Google Sheets
    """Opção S — Escreve os dados locais para o Google Sheet.

    Só funciona se o Google Sheets estiver configurado e ligado (senão
    avisa e volta). Escreve os dados LOCAIS por cima da folha na cloud —
    por isso ao sair o programa pergunta antes de sincronizar (ver main()).
    """
    limpar_ecra()
    cabecalho("SINCRONIZAR COM GOOGLE SHEETS")
    if gsheets is None or not gsheets.conectado:
        print("  Google Sheets não configurado. Verifica .env e credentials.json.")
        pausa()
        return
    gsheets.sincronizar_tudo(gestor)
    pausa()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    """Arranca o programa: carrega config, dados, e inicia o menu."""
    limpar_ecra()
    cabecalho("A INICIAR O GESTOR DE CRONOGRAMA")

    # 1. Configurações
    print("  A carregar configurações...")
    config = carregar_configuracao()

    # 2. Dados — base de dados (SQLite/PostgreSQL) ou JSON local.
    # Se FONTE_DADOS=db, o terminal usa a MESMA base de dados que a web
    # (uma só fonte de verdade: uma alteração aqui aparece já na web).
    engine = None
    if os.environ.get("FONTE_DADOS", "json") == "db":
        import classes.repositorio_db as repositorio_db
        engine = repositorio_db.criar_engine()
        repositorio_db.criar_tabelas(engine)
    gestor = GestorCronograma(pasta_dados="dados", engine=engine)
    gestor.carregar_dados()
    print(f"  Dados: {len(gestor.modulos)} módulos, "
          f"{len(gestor.professores)} professores, "
          f"{len(gestor.formandos)} formandos")

    # 3. Google Sheets (opcional)
    gsheets = None
    if config["gsheets_nome"] != "" and config["gsheets_credenciais"] != "":
        print("\n  A ligar ao Google Sheets...")
        gsheets = GoogleSheetsSync(
            config["gsheets_credenciais"], config["gsheets_nome"]
        )
        gsheets.conectar()
    else:
        print("  Google Sheets: não configurado")

    # 4. Email (opcional)
    email_sender = EmailSender()
    if config["email_remetente"] != "" and config["email_password"] != "":
        email_sender.configurar_gmail(
            config["email_remetente"], config["email_password"]
        )
        if config["email_servidor"] != "":
            email_sender.servidor = config["email_servidor"]
        print("  Email: configurado")
    else:
        print("  Email: não configurado")

    pausa()

    # 5. Menu
    while True:
        limpar_ecra()
        gs_on = gsheets is not None and gsheets.conectado
        em_on = email_sender.configurado
        opcao = mostrar_menu(gs_on, em_on)

        if opcao == "1":
            opcao_ver_cronograma(gestor)
        elif opcao == "2":
            opcao_adicionar_modulo(gestor)
        elif opcao == "3":
            opcao_ver_professores(gestor)
        elif opcao == "4":
            opcao_adicionar_professor(gestor)
        elif opcao == "5":
            opcao_ver_formandos(gestor)
        elif opcao == "6":
            opcao_adicionar_formando(gestor)
        elif opcao == "7":
            opcao_registar_alteracao(gestor, gsheets, email_sender)
        elif opcao == "8":
            opcao_ver_alteracoes(gestor)
        elif opcao == "9":
            opcao_registar_horas(gestor)
        elif opcao == "10":
            opcao_importar_csv(gestor)
        elif opcao == "11":
            opcao_adicionar_avaliacao(gestor)
        elif opcao == "12":
            opcao_remover_formando(gestor)
        elif opcao == "13":
            opcao_lancar_notas(gestor)
        elif opcao == "14":
            opcao_gerar_qr(gestor)
        elif opcao.upper() == "S":
            opcao_sincronizar(gestor, gsheets)
        elif opcao == "0":
            # Sincronizar ao sair passou a ser OPCIONAL e CONFIRMADO.
            # Sincronizar escreve os dados LOCAIS por cima do Google Sheet; se
            # os dados locais estiverem desatualizados, isso apagaria os dados
            # bons na cloud. Por isso perguntamos primeiro, com "não" por
            # defeito (basta carregar Enter para sair sem tocar na cloud).
            if gsheets is not None and gsheets.conectado:
                resposta = input(
                    "\n  Sincronizar os dados locais para o Google Sheets antes de sair?\n"
                    "  ATENÇÃO: escreve os dados locais POR CIMA da cloud. [s/N]: "
                ).strip().lower()
                if resposta == "s":
                    print("  A sincronizar...")
                    gsheets.sincronizar_tudo(gestor)
                else:
                    print("  Sem sincronizar — o Google Sheet ficou como estava.")
            limpar_ecra()
            print("\n  Programa terminado. Até à próxima!\n")
            break
        else:
            print("\n  Opção inválida.")
            pausa()


if __name__ == "__main__":
    main()
