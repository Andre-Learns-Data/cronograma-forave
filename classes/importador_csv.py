# ============================================================
# importador_csv.py — Classe ImportadorCSV
# ============================================================
# Importa dados em massa a partir de ficheiros CSV, em vez de
# os introduzir um a um no terminal. Útil para carregar o
# cronograma inteiro de uma vez (ex: exportar do Excel para CSV).
#
# Autoria: base criada pela Juliana (Sessão 3, branch
#          feature/importacao-csv). Evoluída no Bloco 2:
#   - passou a usar gestor.*_existe() para SALTAR duplicados
#     (antes, importar o mesmo CSV duas vezes criava repetidos)
#   - passou a DEVOLVER um resumo (sem print) — princípio de
#     separação de responsabilidades (secção 5.4): quem chama
#     decide como apresentar "N importados, M saltados, K erros"
#   - estendida a formandos e professores (antes só módulos)
#
# Dependências: csv (stdlib)
#
# Formatos de CSV esperados (primeira linha = cabeçalho):
#   módulos:     nome,professor,horas_totais,horas_dadas,estado
#                (colunas 'ufcd' e 'datas' aceites e opcionais — ex:
#                 ufcd,nome,professor,horas_totais,horas_dadas,estado,datas)
#                'datas' = dias de aula separados por ';'
#                (ex: "09/06/2026;16/06/2026") — carrega o cronograma
#   formandos:   nome,email,modulos          (modulos separados por ';')
#   professores: nome,email,telefone,modulos (modulos separados por ';')
#
# Alinhado com: Aula 7 (try/except), Aula 6 (dicionários, listas)
# ============================================================

import csv


class ImportadorCSV:
    """
    Importa módulos, formandos e professores de ficheiros CSV.

    Cada método de importação devolve um dicionário-resumo com a
    contagem de importados / saltados (duplicados) / erros, mais a
    lista de mensagens de erro. Não imprime nada — segue o princípio
    de separação de responsabilidades (secção 5.4): a apresentação
    fica para quem chama (main.py hoje, GUI/HTML amanhã).
    """

    def _resumo_vazio(self):
        """
        Cria o dicionário-resumo inicial (tudo a zero).

        Retorna:
            dict: {"importados": 0, "saltados": 0, "erros": 0,
                   "erros_detalhe": []}

        Usado pelos três métodos de importação para começarem de um
        estado limpo — evita repetir a mesma estrutura três vezes.
        """
        resumo = {}
        resumo["importados"] = 0
        resumo["saltados"] = 0
        resumo["erros"] = 0
        resumo["erros_detalhe"] = []
        return resumo

    def _texto_para_lista(self, texto):
        """
        Converte uma string "Python;SQL;Redes" numa lista de strings.

        Parâmetros:
            texto (str): Valor da coluna, com itens separados por ';'.
                         Pode ser vazio ou None.

        Retorna:
            list: Lista de nomes (sem espaços extra, sem itens vazios).

        Conceito: padrão lista vazia + for + if + append (Aula 6).
        Usado para a coluna 'modulos' de formandos e professores.
        """
        lista = []

        # Proteger contra célula em branco (DictReader pode devolver None)
        if texto is None:
            return lista

        for parte in texto.split(";"):
            parte = parte.strip()
            if parte != "":
                lista.append(parte)

        return lista

    # --------------------------------------------------------
    # Importar módulos
    # --------------------------------------------------------

    def importar_modulos(self, caminho, gestor):
        """
        Importa módulos de um CSV (cabeçalho: nome,professor,
        horas_totais,horas_dadas,estado).

        Para cada linha:
            - se já existir um módulo com esse nome -> saltar (duplicado)
            - senão -> gestor.adicionar_modulo(...)

        Parâmetros:
            caminho (str): Caminho do ficheiro CSV.
            gestor (GestorCronograma): Onde os módulos são adicionados.

        Retorna:
            dict: Resumo {importados, saltados, erros, erros_detalhe}.

        Evolução (Bloco 2): usa gestor.modulo_existe() (validação da
        Sessão 3) para não duplicar ao reimportar o mesmo ficheiro.
        """
        resumo = self._resumo_vazio()

        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
        except FileNotFoundError:
            resumo["erros"] = resumo["erros"] + 1
            resumo["erros_detalhe"].append("Ficheiro CSV não encontrado.")
            return resumo

        leitor = csv.DictReader(ficheiro)

        # numero_linha começa em 1 (cabeçalho); cada dado incrementa
        numero_linha = 1
        for linha in leitor:
            numero_linha = numero_linha + 1
            try:
                nome = linha["nome"].strip()

                # Saltar duplicados (validação da Sessão 3)
                if gestor.modulo_existe(nome):
                    resumo["saltados"] = resumo["saltados"] + 1
                    continue

                professor = linha["professor"].strip()
                horas_totais = int(linha["horas_totais"])
                horas_dadas = int(linha["horas_dadas"])
                estado = linha["estado"].strip()

                # Coluna 'ufcd' é opcional — se o CSV não a tiver, fica ""
                ufcd = linha.get("ufcd", "")
                if ufcd is None:
                    ufcd = ""
                ufcd = ufcd.strip()

                # Coluna 'datas' é opcional — os dias de aula separados por
                # ';' (ex: "09/06/2026;16/06/2026"). Reusa o mesmo splitter
                # da coluna 'modulos'. Se ausente/vazia, fica sem datas.
                datas = self._texto_para_lista(linha.get("datas", ""))

                gestor.adicionar_modulo(
                    nome, professor, horas_totais, horas_dadas, estado, datas, ufcd=ufcd
                )
                resumo["importados"] = resumo["importados"] + 1

            except Exception as erro:
                resumo["erros"] = resumo["erros"] + 1
                resumo["erros_detalhe"].append(f"Linha {numero_linha}: {erro}")

        ficheiro.close()
        return resumo

    # --------------------------------------------------------
    # Importar formandos
    # --------------------------------------------------------

    def importar_formandos(self, caminho, gestor):
        """
        Importa formandos de um CSV (cabeçalho: nome,email,modulos).

        A coluna 'modulos' é uma lista separada por ';'
        (ex: "Python;SQL"). Pode ficar vazia.

        Duplicados são detectados pelo email (chave única — Sessão 2).

        Parâmetros:
            caminho (str): Caminho do ficheiro CSV.
            gestor (GestorCronograma): Onde os formandos são adicionados.

        Retorna:
            dict: Resumo {importados, saltados, erros, erros_detalhe}.
        """
        resumo = self._resumo_vazio()

        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
        except FileNotFoundError:
            resumo["erros"] = resumo["erros"] + 1
            resumo["erros_detalhe"].append("Ficheiro CSV não encontrado.")
            return resumo

        leitor = csv.DictReader(ficheiro)

        numero_linha = 1
        for linha in leitor:
            numero_linha = numero_linha + 1
            try:
                email = linha["email"].strip()

                # Saltar duplicados pelo email (chave única — Sessão 2)
                if gestor.formando_existe(email):
                    resumo["saltados"] = resumo["saltados"] + 1
                    continue

                nome = linha["nome"].strip()
                modulos = self._texto_para_lista(linha.get("modulos", ""))

                gestor.adicionar_formando(nome, email, modulos)
                resumo["importados"] = resumo["importados"] + 1

            except Exception as erro:
                resumo["erros"] = resumo["erros"] + 1
                resumo["erros_detalhe"].append(f"Linha {numero_linha}: {erro}")

        ficheiro.close()
        return resumo

    # --------------------------------------------------------
    # Importar professores
    # --------------------------------------------------------

    def importar_professores(self, caminho, gestor):
        """
        Importa professores de um CSV
        (cabeçalho: nome,email,telefone,modulos).

        A coluna 'modulos' é uma lista separada por ';'. Pode ficar
        vazia. Duplicados são detectados pelo email (Sessão 2).

        Parâmetros:
            caminho (str): Caminho do ficheiro CSV.
            gestor (GestorCronograma): Onde os professores são adicionados.

        Retorna:
            dict: Resumo {importados, saltados, erros, erros_detalhe}.
        """
        resumo = self._resumo_vazio()

        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
        except FileNotFoundError:
            resumo["erros"] = resumo["erros"] + 1
            resumo["erros_detalhe"].append("Ficheiro CSV não encontrado.")
            return resumo

        leitor = csv.DictReader(ficheiro)

        numero_linha = 1
        for linha in leitor:
            numero_linha = numero_linha + 1
            try:
                email = linha["email"].strip()

                # Saltar duplicados pelo email (chave única — Sessão 2)
                if gestor.professor_existe(email):
                    resumo["saltados"] = resumo["saltados"] + 1
                    continue

                nome = linha["nome"].strip()
                telefone = linha.get("telefone", "").strip()
                modulos = self._texto_para_lista(linha.get("modulos", ""))

                gestor.adicionar_professor(nome, email, telefone, modulos)
                resumo["importados"] = resumo["importados"] + 1

            except Exception as erro:
                resumo["erros"] = resumo["erros"] + 1
                resumo["erros_detalhe"].append(f"Linha {numero_linha}: {erro}")

        ficheiro.close()
        return resumo
