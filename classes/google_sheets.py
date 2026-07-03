# ============================================================
# google_sheets.py — Integração com Google Sheets
# ============================================================
# Este módulo liga o programa ao Google Sheets via API.
# A spreadsheet funciona como uma "base de dados na cloud"
# que qualquer pessoa com o link pode consultar no browser.
#
# Pré-requisitos (feitos uma única vez):
#   1. Criar projecto no Google Cloud Console
#   2. Activar a Google Sheets API
#   3. Criar Service Account e fazer download do credentials.json
#   4. Partilhar a spreadsheet com o email do Service Account
#
# Dependências: pip install gspread google-auth
#
# IMPORTANTE: O ficheiro credentials.json contém dados
# sensíveis — NUNCA vai para o GitHub.
# ============================================================

import json

import gspread


class GoogleSheetsSync:
    """
    Gere a sincronização entre o programa e o Google Sheets.

    Atributos:
        credenciais_path (str): Caminho para o credentials.json.
        spreadsheet_nome (str): Nome da spreadsheet no Google Drive.
        cliente (gspread.Client): Ligação autenticada ao Google.
        spreadsheet (gspread.Spreadsheet): A spreadsheet aberta.
        conectado (bool): Se a ligação está activa.
    """

    def __init__(self, credenciais_path, spreadsheet_id_ou_nome):
        """
        Construtor — configura a ligação (sem conectar ainda).

        Parâmetros:
            credenciais_path (str): Caminho para o ficheiro
                                    credentials.json do Google.
            spreadsheet_id_ou_nome (str): ID ou Nome da spreadsheet.
                                          - Se tiver '/' é um ID
                                          - Caso contrário, é um Nome
        """
        self.credenciais_path = credenciais_path
        self.spreadsheet_id_ou_nome = spreadsheet_id_ou_nome
        self.cliente = None
        self.spreadsheet = None
        self.conectado = False

    # --------------------------------------------------------
    # Ligação
    # --------------------------------------------------------

    def conectar(self):
        """
        Estabelece a ligação ao Google Sheets.

        Usa o ficheiro credentials.json para autenticar
        com uma Service Account. 
        
        Detecta automaticamente se spreadsheet_id_ou_nome é:
        - Um ID (contém caracteres como '/' ou tem 50+ caracteres)
        - Um Nome (texto simples)

        Retorna:
            bool: True se a ligação foi estabelecida.
        """
        try:
            # gspread.service_account() lê o credentials.json
            # e autentica automaticamente com o Google
            self.cliente = gspread.service_account(
                filename=self.credenciais_path
            )

            # Detectar se é ID ou Nome
            spreadsheet_input = self.spreadsheet_id_ou_nome
            
            # Se contém '/' ou tem muito caracteres, é provavelmente um ID
            if '/' in spreadsheet_input or len(spreadsheet_input) > 40:
                # Tentar abrir por ID
                print("  Tentando abrir spreadsheet por ID...")
                self.spreadsheet = self.cliente.open_by_key(spreadsheet_input)
            else:
                # Tentar abrir por Nome
                print(f"  Tentando abrir spreadsheet por Nome: '{spreadsheet_input}'")
                self.spreadsheet = self.cliente.open(spreadsheet_input)

            self.conectado = True
            print(f"  [OK] Google Sheets: ligação estabelecida com '{self.spreadsheet.title}'")
            return True

        except FileNotFoundError:
            print(f"  [ERRO] Google Sheets: ficheiro '{self.credenciais_path}' não encontrado.")
            print("  Passos para resolver:")
            print("    1. Aceder a https://console.cloud.google.com")
            print("    2. Criar uma Service Account")
            print("    3. Fazer download do credentials.json")
            print("    4. Colocar em 'classes/credentials.json'")
            self.conectado = False
            return False

        except gspread.exceptions.SpreadsheetNotFound as e:
            print(f"  [ERRO] Google Sheets: spreadsheet '{self.spreadsheet_id_ou_nome}' não encontrada.")
            print("  Passos para resolver:")
            print("    1. Verificar se o ID/Nome está correto")
            print(f"    2. Partilhar a spreadsheet com: {self.cliente.auth.service_account_email}")
            print(f"    Erro: {e}")
            self.conectado = False
            return False

        except gspread.exceptions.APIError as e:
            print(f"  [ERRO] Google Sheets: erro de API — {e}")
            print("  Verifique as credenciais e permissões")
            self.conectado = False
            return False

        except Exception as erro:
            print(f"  [ERRO] Google Sheets: erro na ligação — {type(erro).__name__}: {erro}")
            print("  A continuar sem sincronização com Google Sheets.")
            self.conectado = False
            return False

    # --------------------------------------------------------
    # Obter ou criar separador (worksheet/tab)
    # --------------------------------------------------------

    def obter_separador(self, nome):
        """
        Obtém um separador (tab) da spreadsheet pelo nome.
        Se não existir, cria um novo.

        Parâmetros:
            nome (str): Nome do separador (ex: "Módulos").

        Retorna:
            gspread.Worksheet: O separador encontrado ou criado.
            None: Se não estiver conectado.
        """
        if not self.conectado:
            return None

        try:
            # Tentar abrir o separador pelo nome
            separador = self.spreadsheet.worksheet(nome)
            return separador
        except gspread.exceptions.WorksheetNotFound:
            # Se não existe, criar com 100 linhas e 20 colunas
            separador = self.spreadsheet.add_worksheet(
                title=nome, rows=100, cols=20
            )
            return separador

    # --------------------------------------------------------
    # Sincronizar dados — escrever na spreadsheet
    # --------------------------------------------------------

    def sincronizar_modulos(self, lista_modulos):
        """
        Escreve a lista de módulos no separador "Módulos".

        Limpa o separador e reescreve tudo de novo —
        abordagem simples e segura para o volume de dados
        que temos (~10 módulos).

        Parâmetros:
            lista_modulos (list): Lista de objectos Modulo.
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Módulos")
        if separador is None:
            return

        # Construir a tabela: cabeçalho + linhas de dados
        # Cada linha é uma lista de valores
        tabela = []

        # Cabeçalho (coluna "UFCD" acrescentada no Bloco 3)
        # Cabeçalho (coluna "UFCD" acrescentada no Bloco 3; "Sessoes" — as
        # aulas com horas + "realizada" em JSON — acrescentada com a feature
        # das horas por sessão). "Datas" mantém-se por retrocompatibilidade
        # e leitura humana; "Sessoes" é a fonte completa.
        cabecalho = ["UFCD", "Nome", "Professor", "Horas Totais",
                      "Horas Dadas", "Horas Restantes",
                      "Progresso (%)", "Estado", "Datas", "Sessoes"]
        tabela.append(cabecalho)

        # Uma linha por módulo
        for m in lista_modulos:
            datas_texto = ", ".join(m.datas)
            linha = [
                m.ufcd,
                m.nome,
                m.professor,
                m.horas_totais,
                m.horas_dadas,
                m.horas_restantes(),
                round(m.percentagem_concluida(), 1),
                m.estado,
                datas_texto,
                json.dumps(m.sessoes_para_persistir(), ensure_ascii=False)
            ]
            tabela.append(linha)

        # Limpar o separador e escrever tudo de uma vez
        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: módulos sincronizados.")

    def sincronizar_professores(self, lista_professores):
        """
        Escreve a lista de professores no separador "Professores".

        Parâmetros:
            lista_professores (list): Lista de objectos Professor.
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Professores")
        if separador is None:
            return

        tabela = []
        cabecalho = ["Nome", "Email", "Telefone", "Módulos"]
        tabela.append(cabecalho)

        for p in lista_professores:
            modulos_texto = ", ".join(p.modulos)
            linha = [p.nome, p.email, p.telefone, modulos_texto]
            tabela.append(linha)

        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: professores sincronizados.")

    def sincronizar_formandos(self, lista_formandos):
        """
        Escreve a lista de formandos no separador "Formandos".

        Parâmetros:
            lista_formandos (list): Lista de objectos Formando.
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Formandos")
        if separador is None:
            return

        tabela = []
        cabecalho = ["Nome", "Email", "Módulos Inscritos"]
        tabela.append(cabecalho)

        for f in lista_formandos:
            modulos_texto = ", ".join(f.modulos)
            linha = [f.nome, f.email, modulos_texto]
            tabela.append(linha)

        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: formandos sincronizados.")

    def sincronizar_alteracoes(self, lista_alteracoes):
        """
        Escreve o histórico de alterações no separador "Alterações".

        Parâmetros:
            lista_alteracoes (list): Lista de objectos Alteracao.
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Alterações")
        if separador is None:
            return

        tabela = []
        cabecalho = ["Data Registo", "Módulo", "Data Original",
                      "Nova Data", "Motivo", "Registado Por"]
        tabela.append(cabecalho)

        for a in lista_alteracoes:
            linha = [
                a.data_registo,
                a.modulo_nome,
                a.data_original,
                a.data_nova,
                a.motivo,
                a.autor
            ]
            tabela.append(linha)

        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: alterações sincronizadas.")

    def sincronizar_avaliacoes(self, lista_modulos):
        """
        Escreve todas as avaliações no separador "Avaliações".

        Como as avaliações vivem dentro de cada módulo, percorremos
        os módulos e, para cada um, as suas avaliações — uma linha
        por momento de avaliação. É mais expressivo do que concatenar
        as avaliações numa célula da tab "Módulos".

        Parâmetros:
            lista_modulos (list): Lista de objectos Modulo.

        (Bloco 3)
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Avaliações")
        if separador is None:
            return

        tabela = []
        cabecalho = ["Módulo", "UFCD", "Data", "Tipo", "Descrição",
                      "Objectivo", "Deliverables", "Peso"]
        tabela.append(cabecalho)

        # Padrão for dentro de for: para cada módulo, as suas avaliações
        for m in lista_modulos:
            for av in m.avaliacoes:
                # O peso é opcional — mostrar "" em vez de None na folha
                if av.peso is None:
                    peso_texto = ""
                else:
                    peso_texto = av.peso

                linha = [
                    m.nome,
                    m.ufcd,
                    av.data,
                    av.tipo,
                    av.descricao,
                    av.objectivo,
                    av.deliverables,
                    peso_texto
                ]
                tabela.append(linha)

        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: avaliações sincronizadas.")

    def sincronizar_notas(self, lista_modulos):
        """
        Escreve todas as notas (classificações) no separador "Notas".

        As notas vivem dentro de cada avaliação (av.notas = {email: nota}).
        Percorremos os módulos -> avaliações -> notas e geramos uma linha
        por (avaliação, aluno) com nota lançada.

        IMPORTANTE — a coluna "Indice" é a posição da avaliação dentro do
        módulo (0, 1, 2...). É a mesma ordem usada em sincronizar_avaliacoes
        (percorremos m.avaliacoes pela ordem). É essa correspondência que
        permite, ao reconstruir o gestor a partir do Sheet, voltar a ligar
        cada nota à avaliação certa (ver classes/carregador_sheets.py).

        ATENÇÃO RGPD: esta tab contém emails + notas (dados pessoais
        sensíveis). A spreadsheet é PRIVADA (partilhada só com a Service
        Account e o coordenador) — NUNCA deve ser publicada na web. Só o
        dashboard alojado e autenticado lê estas notas, e cada aluno só vê
        as suas (ver app.py / dados_aluno).

        Parâmetros:
            lista_modulos (list): Lista de objectos Modulo.

        (Bloco 4 / Fase B — fonte de dados do dashboard alojado)
        """
        if not self.conectado:
            return

        separador = self.obter_separador("Notas")
        if separador is None:
            return

        tabela = []
        cabecalho = ["Módulo", "Indice", "Data", "Email Aluno", "Nota"]
        tabela.append(cabecalho)

        # for (módulos) -> for (avaliações, com índice) -> for (notas)
        for m in lista_modulos:
            indice = 0
            for av in m.avaliacoes:
                # av.notas é um dict {email: nota}; percorrer as chaves
                for email in av.notas:
                    linha = [m.nome, indice, av.data, email, av.notas[email]]
                    tabela.append(linha)
                indice = indice + 1

        separador.clear()
        separador.update(tabela)
        print("  Google Sheets: notas sincronizadas.")

    # --------------------------------------------------------
    # Obter dados — ler da spreadsheet
    # --------------------------------------------------------

    def obter_cronograma(self):
        """
        Obtém todos os módulos do separador "Módulos".

        Retorna:
            list: Lista de dicionários com dados do cronograma.
                  Vazio se não conectado ou separador não existe.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Módulos")
            if separador is None:
                return []
            
            registos = separador.get_all_records()
            return registos
        except Exception as e:
            print(f"  Google Sheets: erro ao obter cronograma — {e}")
            return []

    def obter_alteracoes(self):
        """
        Obtém todos os registos de alterações do separador "Alterações".

        Retorna:
            list: Lista de dicionários com registos de alterações.
                  Vazio se não conectado ou separador não existe.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Alterações")
            if separador is None:
                return []
            
            registos = separador.get_all_records()
            return registos
        except Exception as e:
            print(f"  Google Sheets: erro ao obter alterações — {e}")
            return []

    def obter_professores(self):
        """
        Obtém todos os professores do separador "Professores".

        Retorna:
            list: Lista de dicionários com dados dos professores.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Professores")
            if separador is None:
                return []
            
            registos = separador.get_all_records()
            return registos
        except Exception as e:
            print(f"  Google Sheets: erro ao obter professores — {e}")
            return []

    def obter_avaliacoes(self):
        """
        Obtém todas as avaliações do separador "Avaliações".

        Retorna:
            list: Lista de dicionários (uma por momento de avaliação).
                  Vazio se não conectado ou separador não existe.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Avaliações")
            if separador is None:
                return []

            return separador.get_all_records()
        except Exception as e:
            print(f"  Google Sheets: erro ao obter avaliações — {e}")
            return []

    def obter_formandos(self):
        """
        Obtém todos os formandos do separador "Formandos".

        Retorna:
            list: Lista de dicionários com os formandos.
                  Vazio se não conectado ou separador não existe.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Formandos")
            if separador is None:
                return []

            return separador.get_all_records()
        except Exception as e:
            print(f"  Google Sheets: erro ao obter formandos — {e}")
            return []

    def obter_notas(self):
        """
        Obtém todas as notas do separador "Notas".

        Retorna:
            list: Lista de dicionários (uma por nota lançada), com as
                  chaves "Módulo", "Indice", "Data", "Email Aluno", "Nota".
                  Vazio se não conectado ou separador não existe.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Notas")
            if separador is None:
                return []

            return separador.get_all_records()
        except Exception as e:
            print(f"  Google Sheets: erro ao obter notas — {e}")
            return []

    def obter_utilizadores(self):
        """
        Obtém as contas de acesso do separador "Utilizadores".

        Usado quando o dashboard está alojado: as contas dos alunos
        vivem no Sheet (e não num ficheiro local do servidor), para
        sobreviverem a qualquer reinício/redeploy do alojamento.

        Retorna:
            list: Lista de dicionários com chaves "Email",
                  "Password Hash", "Papel". Vazio se não conectado.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Utilizadores")
            if separador is None:
                return []

            # Ler em bruto e mapear por POSIÇÃO das colunas
            # (col 0 = email, col 1 = hash, col 2 = papel). NÃO usamos
            # get_all_records()/cabeçalho de propósito: se faltasse o
            # cabeçalho, o get_all_records confundia a 1ª conta com o
            # cabeçalho e partia o login. Ler por posição é robusto.
            registos = []
            for linha in separador.get_all_values():
                if len(linha) < 2:
                    continue
                email = linha[0].strip()
                # Saltar linhas vazias e uma eventual linha de cabeçalho
                if email == "" or email == "Email":
                    continue
                if len(linha) >= 3 and linha[2].strip() != "":
                    papel = linha[2].strip()
                else:
                    papel = "aluno"
                registos.append({
                    "Email": email,
                    "Password Hash": linha[1],
                    "Papel": papel
                })
            return registos
        except Exception as e:
            print(f"  Google Sheets: erro ao obter utilizadores — {e}")
            return []

    def acrescentar_utilizador(self, email, password_hash, papel="aluno"):
        """
        Acrescenta UMA conta nova ao separador "Utilizadores".

        Usa append_row (acrescenta uma linha) em vez de reescrever tudo —
        assim dois registos quase simultâneos não se sobrepõem. Garante o
        cabeçalho na primeira vez (quando a tab ainda está vazia).

        Parâmetros:
            email (str): Email da conta.
            password_hash (str): Hash da password (nunca a password).
            papel (str): Papel da conta ("aluno" por defeito).

        Retorna:
            bool: True se acrescentou, False se não estava conectado.

        (Bloco 4 / Fase C — contas no Sheet, para o alojamento)
        """
        if not self.conectado:
            return False

        separador = self.obter_separador("Utilizadores")
        if separador is None:
            return False

        # Acrescentar uma linha [email, hash, papel]. Não escrevemos um
        # cabeçalho aqui de propósito: a leitura (obter_utilizadores) é
        # posicional e não depende de cabeçalho, o que torna o registo
        # robusto (o cabeçalho frágil partia o login — ver obter_utilizadores).
        separador.append_row([email, password_hash, papel])
        return True

    def atualizar_password_utilizador(self, email, novo_hash):
        """
        Actualiza o hash da password de uma conta já existente.

        Usado na reposição de password ("esqueci-me"): procura a linha do
        utilizador pelo email e reescreve só a célula do hash (coluna 2),
        deixando email e papel intactos.

        Parâmetros:
            email (str): Email da conta a actualizar.
            novo_hash (str): Novo hash da password (nunca a password).

        Retorna:
            bool: True se actualizou, False se não estava conectado ou se
                  não encontrou a conta.

        (Nível 2 — reposição de password)
        """
        if not self.conectado:
            return False

        separador = self.obter_separador("Utilizadores")
        if separador is None:
            return False

        # Procurar a linha pelo email. As linhas do gspread são 1-based
        # (a primeira linha é a 1), por isso o enumerate começa em 1.
        linhas = separador.get_all_values()
        for indice, linha in enumerate(linhas, start=1):
            if len(linha) >= 1 and linha[0].strip() == email:
                separador.update_cell(indice, 2, novo_hash)  # coluna 2 = hash
                return True

        return False

    # --------------------------------------------------------
    # Auditoria — registo append-only de "quem fez o quê"
    # --------------------------------------------------------

    def acrescentar_auditoria(self, data_hora, autor, accao, detalhe):
        """
        Acrescenta UMA entrada ao separador "Auditoria".

        Usa append_row (acrescenta uma linha) — nunca reescreve nem
        apaga: é um registo de accountability, só cresce. Segue o mesmo
        padrão robusto de acrescentar_utilizador (sem cabeçalho frágil;
        a leitura é posicional).

        Parâmetros:
            data_hora (str): Data e hora da acção ("dd/mm/aaaa HH:MM").
            autor (str): Quem fez (email do coordenador).
            accao (str): Tipo de acção (ex: "Lançar notas").
            detalhe (str): Descrição legível do que mudou.

        Retorna:
            bool: True se acrescentou, False se não estava conectado.
        """
        if not self.conectado:
            return False

        separador = self.obter_separador("Auditoria")
        if separador is None:
            return False

        separador.append_row([data_hora, autor, accao, detalhe])
        return True

    def obter_auditoria(self):
        """
        Obtém as entradas do separador "Auditoria".

        Lê por POSIÇÃO das colunas (col 0 = data/hora, 1 = autor,
        2 = acção, 3 = detalhe), tal como obter_utilizadores — assim
        não depende de um cabeçalho (que poderia faltar) e é robusto.

        Retorna:
            list: Lista de dicionários com as chaves data_hora, autor,
                  accao, detalhe. Vazia se não conectado.
        """
        if not self.conectado:
            return []

        try:
            separador = self.obter_separador("Auditoria")
            if separador is None:
                return []

            registos = []
            for linha in separador.get_all_values():
                if len(linha) < 4:
                    continue
                # Saltar uma eventual linha de cabeçalho
                if linha[0].strip() in ("", "Data/Hora"):
                    continue
                registos.append({
                    "data_hora": linha[0],
                    "autor": linha[1],
                    "accao": linha[2],
                    "detalhe": linha[3],
                })
            return registos
        except Exception as e:
            print(f"  Google Sheets: erro ao obter auditoria — {e}")
            return []

    def sincronizar_tudo(self, gestor):
        """
        Sincroniza todas as entidades de uma só vez.

        Parâmetros:
            gestor: Objecto GestorCronograma com todos os dados.
        """
        if not self.conectado:
            print("  Google Sheets: sem ligação — sincronização ignorada.")
            return

        print()
        self.sincronizar_modulos(gestor.modulos)
        self.sincronizar_professores(gestor.professores)
        self.sincronizar_formandos(gestor.formandos)
        self.sincronizar_alteracoes(gestor.alteracoes)
        self.sincronizar_avaliacoes(gestor.modulos)
        self.sincronizar_notas(gestor.modulos)
        print("  Google Sheets: sincronização completa.")
