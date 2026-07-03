# ============================================================
# fakes.py — Dublês de teste do Google Sheets (sem rede)
# ============================================================
# Imitam o suficiente do gspread para testar a sincronização e a
# reconstrução SEM precisar de internet nem de credenciais. Guardam
# as tabelas em memória, tal como uma spreadsheet faria.
# ============================================================

import gspread


class FakeWorksheet:
    """Imita um separador (tab) do gspread, guardando a tabela em memória."""

    def __init__(self):
        self.tabela = []

    def clear(self):
        self.tabela = []

    def update(self, tabela):
        self.tabela = tabela

    def append_row(self, linha):
        self.tabela.append(linha)

    def update_cell(self, linha, coluna, valor):
        # Índices 1-based, como no gspread (linha 1 = primeira).
        self.tabela[linha - 1][coluna - 1] = valor

    def get_all_values(self):
        return self.tabela

    def get_all_records(self):
        # Primeira linha = cabeçalho; as seguintes = dados (como o gspread)
        if len(self.tabela) < 1:
            return []
        cabecalho = self.tabela[0]
        registos = []
        for linha in self.tabela[1:]:
            registo = {}
            for i in range(len(cabecalho)):
                registo[cabecalho[i]] = linha[i] if i < len(linha) else ""
            registos.append(registo)
        return registos


class FakeSpreadsheet:
    """Imita uma spreadsheet do gspread: um conjunto de tabs por nome."""

    def __init__(self):
        self.tabs = {}

    def worksheet(self, nome):
        if nome not in self.tabs:
            raise gspread.exceptions.WorksheetNotFound
        return self.tabs[nome]

    def add_worksheet(self, title, rows, cols):
        ws = FakeWorksheet()
        self.tabs[title] = ws
        return ws


def fake_gsheets():
    """
    Devolve um GoogleSheetsSync ligado a uma spreadsheet falsa.

    Usa o código REAL do GoogleSheetsSync (sincronizar_*, obter_*),
    apenas com a spreadsheet substituída por uma em memória — por isso
    os testes exercitam o caminho verdadeiro, sem rede.
    """
    from classes.google_sheets import GoogleSheetsSync
    gs = GoogleSheetsSync("creds-falsas", "id-falso")
    gs.conectado = True
    gs.spreadsheet = FakeSpreadsheet()
    return gs
