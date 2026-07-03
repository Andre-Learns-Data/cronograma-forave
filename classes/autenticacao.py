# ============================================================
# autenticacao.py — Classe GestorAutenticacao
# ============================================================
# Gere as contas de acesso à área web autenticada (área do
# aluno). Responsável por:
#   - Guardar/carregar os utilizadores em dados/utilizadores.json
#   - Registar uma conta nova (com password "hasheada")
#   - Autenticar (verificar email + password no login)
#
# SEGURANÇA — porque é que NÃO guardamos a password em texto:
#   Guardar passwords em texto simples é um erro grave: quem
#   abrisse o ficheiro via todas as passwords da turma. Em vez
#   disso guardamos um "hash" — uma impressão digital
#   irreversível. No login, voltamos a "hashear" o que o aluno
#   escreveu e comparamos os hashes. Nunca se desfaz o hash.
#
#   Usamos o werkzeug.security (já vem instalado com o Flask):
#     - generate_password_hash(password) -> calcula o hash
#     - check_password_hash(hash, password) -> compara (True/False)
#
# Conceitos das aulas aplicados:
#   - Classes e métodos (Aula 5)
#   - Dicionários e listas (Aula 6)
#   - open()/close() + json (Sessão Online 6)
#   - try/except FileNotFoundError (Aula 7)
#
# Criada na: Bloco 4 / Nível 2 (login + área do aluno)
# ============================================================

import json

# itsdangerous também vem com o Flask. Serve para assinar os "tokens" de
# reposição de password: um texto curto, assinado com a chave secreta da
# aplicação, que viaja no link enviado por email. Como é ASSINADO, ninguém
# o pode falsificar; e como é TEMPORIZADO (URLSafeTimedSerializer), expira
# sozinho passado um tempo. Nada é guardado em disco — o próprio link é a
# prova (ideal para alojamento com disco efémero, ex: Render).
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# werkzeug é uma dependência do Flask — não é preciso instalar nada novo.
from werkzeug.security import check_password_hash, generate_password_hash

from classes.utilizador import Utilizador, utilizador_from_dict


class GestorAutenticacao:
    """
    Gere as contas de acesso (registo, login, persistência).

    Atributos:
        caminho (str): Caminho do ficheiro JSON dos utilizadores.
        utilizadores (list): Lista de objectos Utilizador em memória.
    """

    def __init__(self, caminho="dados/utilizadores.json", gsheets=None, secret=None):
        """
        Construtor — define o backend e carrega os utilizadores.

        Tem dois modos (escolhidos automaticamente):
          - JSON local (por defeito): contas em dados/utilizadores.json.
            É o que se usa em desenvolvimento, no PC do coordenador.
          - Google Sheet: se for passado um GoogleSheetsSync já conectado,
            as contas vivem na tab "Utilizadores" do Sheet. É o que se usa
            quando o dashboard está ALOJADO — assim as contas sobrevivem a
            reinícios/redeploys do servidor (cujo disco pode ser efémero).

        Parâmetros:
            caminho (str): Ficheiro JSON (modo local). Protegido pelo
                           .gitignore — nunca vai para o GitHub.
            gsheets (GoogleSheetsSync): ligação já conectada (modo Sheet).
                                        Se None ou não conectado, usa JSON.
            secret (str): Chave secreta usada para assinar os tokens de
                          reposição de password (normalmente a secret_key
                          do Flask). Só é precisa para a função "esqueci-me
                          da password"; o login/registo não a usam.
        """
        self.caminho = caminho
        self.gsheets = gsheets
        # Modo Sheet só se houver ligação conectada; senão, JSON local.
        self.modo_sheets = gsheets is not None and getattr(gsheets, "conectado", False)
        # Fallback de desenvolvimento: se não for dada uma chave, usa-se uma
        # constante. Em produção a app passa a secret_key real (do ambiente).
        self.secret = secret or "dev-reposicao-key-mudar"
        self.utilizadores = []
        self.carregar()

    # --------------------------------------------------------
    # Persistência — guardar e carregar (JSON)
    # --------------------------------------------------------

    def carregar(self):
        """
        Carrega os utilizadores do backend activo (Sheet ou JSON).

        Modo Sheet: lê a tab "Utilizadores" (chaves "Email",
        "Password Hash", "Papel"). Modo JSON: lê o ficheiro local; se
        não existir (primeira vez), a lista fica vazia — sem erro.
        """
        self.utilizadores = []

        if self.modo_sheets:
            for reg in self.gsheets.obter_utilizadores():
                email = reg.get("Email", "")
                password_hash = reg.get("Password Hash", "")
                papel = reg.get("Papel", "aluno")
                if email == "":
                    continue
                if papel == "":
                    papel = "aluno"
                self.utilizadores.append(Utilizador(email, password_hash, papel))
            return

        try:
            ficheiro = open(self.caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                self.utilizadores.append(utilizador_from_dict(d))
        except FileNotFoundError:
            pass  # Ainda não há contas — lista fica vazia.

    def guardar(self):
        """
        Grava todos os utilizadores no ficheiro JSON.

        Conceito: padrão lista vazia + for + append, mas em vez de
        texto guardamos o dicionário de cada utilizador (to_dict()).
        """
        lista_dicts = []
        for u in self.utilizadores:
            lista_dicts.append(u.to_dict())

        ficheiro = open(self.caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

    # --------------------------------------------------------
    # Consulta
    # --------------------------------------------------------

    def email_registado(self, email):
        """
        Verifica se já existe uma conta com este email.

        Parâmetros:
            email (str): Email a verificar.

        Retorna:
            bool: True se já existe conta, False se não.

        Conceito: padrão for + if com flag variable (Aula 6).
        """
        existe = False
        for u in self.utilizadores:
            if u.email == email:
                existe = True

        return existe

    def procurar(self, email):
        """
        Procura um utilizador pelo email.

        Parâmetros:
            email (str): Email a procurar.

        Retorna:
            Utilizador ou None: O utilizador se existir, senão None.
        """
        for u in self.utilizadores:
            if u.email == email:
                return u

        return None

    # --------------------------------------------------------
    # Registo e autenticação
    # --------------------------------------------------------

    def registar(self, email, password, papel="aluno"):
        """
        Cria uma conta nova com a password já "hasheada".

        ATENÇÃO: esta função NÃO valida se o email pertence a um
        formando — essa validação é feita por quem chama (a rota
        web), porque depende da lista de formandos do gestor.
        Aqui só tratamos da conta em si.

        Parâmetros:
            email (str): Email (chave única).
            password (str): Password em texto (será convertida em hash).
            papel (str): Papel da conta. Por defeito "aluno".

        Retorna:
            Utilizador ou None: A conta criada, ou None se já existir
                                uma conta com esse email.
        """
        # Não permitir duas contas com o mesmo email
        if self.email_registado(email):
            return None

        # Calcular o hash da password (nunca guardamos a password em si)
        password_hash = generate_password_hash(password)

        utilizador = Utilizador(email, password_hash, papel)
        self.utilizadores.append(utilizador)

        # Persistir no backend activo
        if self.modo_sheets:
            self.gsheets.acrescentar_utilizador(email, password_hash, papel)
        else:
            self.guardar()

        return utilizador

    def autenticar(self, email, password):
        """
        Verifica as credenciais de login.

        Procura a conta pelo email e compara a password escrita
        com o hash guardado (check_password_hash). Nunca se
        "desfaz" o hash — comparam-se hashes.

        Parâmetros:
            email (str): Email introduzido no login.
            password (str): Password introduzida no login.

        Retorna:
            Utilizador ou None: O utilizador se as credenciais
                                estiverem certas, senão None.
        """
        utilizador = self.procurar(email)
        if utilizador is None:
            return None

        if check_password_hash(utilizador.password_hash, password):
            return utilizador

        return None

    # --------------------------------------------------------
    # Reposição de password ("esqueci-me da password")
    # --------------------------------------------------------
    #
    # Como funciona, em três passos:
    #   1. O aluno pede a reposição (escreve o email).
    #   2. Geramos um TOKEN assinado e temporizado e enviamos, por email,
    #      um link que o contém. O token NÃO é guardado em lado nenhum —
    #      é "stateless": a assinatura é a prova de que é legítimo.
    #   3. O aluno abre o link, escreve a nova password, e validamos o
    #      token antes de a aceitar.
    #
    # USO ÚNICO sem guardar nada: dentro do token metemos uma "impressão
    # digital" do hash actual da password (os últimos caracteres). Quando a
    # password muda, o hash muda, e essa impressão deixa de bater certo — por
    # isso um link já usado (ou um link antigo) deixa automaticamente de
    # funcionar, sem precisarmos de uma lista de tokens gastos.

    def _serializador(self):
        """Cria o assinador de tokens (chave secreta + 'sal' fixo)."""
        return URLSafeTimedSerializer(self.secret, salt="reposicao-password")

    def criar_token_reposicao(self, email):
        """
        Gera um token de reposição para um email registado.

        Parâmetros:
            email (str): Email da conta.

        Retorna:
            str ou None: O token assinado, ou None se não existir conta
                         com esse email (a rota web responde sempre com a
                         mesma mensagem neutra, para não revelar quem tem
                         conta — mas internamente só geramos para contas reais).
        """
        utilizador = self.procurar(email)
        if utilizador is None:
            return None

        # Impressão digital do hash actual: torna o token de uso único.
        carga = {"email": email, "h": utilizador.password_hash[-12:]}
        return self._serializador().dumps(carga)

    def validar_token_reposicao(self, token, validade_segundos=3600):
        """
        Verifica um token de reposição e devolve o email a que pertence.

        Falha (devolve None) se o token: estiver corrompido/falsificado,
        tiver expirado (por defeito 1 hora), a conta já não existir, ou a
        password já tiver sido mudada desde que o link foi gerado.

        Parâmetros:
            token (str): O token vindo do link.
            validade_segundos (int): Tempo de validade. Por defeito 3600 (1h).

        Retorna:
            str ou None: O email se o token for válido, senão None.
        """
        try:
            carga = self._serializador().loads(token, max_age=validade_segundos)
        except (BadSignature, SignatureExpired):
            return None

        if not isinstance(carga, dict):
            return None

        email = carga.get("email", "")
        impressao = carga.get("h", "")

        utilizador = self.procurar(email)
        if utilizador is None:
            return None

        # Se a password já mudou desde que o link foi gerado, recusar (uso único).
        if utilizador.password_hash[-12:] != impressao:
            return None

        return email

    def redefinir_password(self, email, nova_password):
        """
        Define uma nova password para uma conta existente.

        Calcula o novo hash, actualiza-o em memória e persiste no backend
        activo (ficheiro JSON ou tab "Utilizadores" do Sheet). Mudar o hash
        invalida automaticamente quaisquer tokens de reposição antigos.

        Parâmetros:
            email (str): Email da conta.
            nova_password (str): Nova password em texto (será "hasheada").

        Retorna:
            Utilizador ou None: A conta actualizada, ou None se não existir.
        """
        utilizador = self.procurar(email)
        if utilizador is None:
            return None

        novo_hash = generate_password_hash(nova_password)
        utilizador.password_hash = novo_hash

        # Persistir no backend activo
        if self.modo_sheets:
            self.gsheets.atualizar_password_utilizador(email, novo_hash)
        else:
            self.guardar()

        return utilizador
