# ============================================================
# app.py — Dashboard web (Flask) do Gestor de Cronograma
# ============================================================
# Servidor web que mostra, de forma visual, os DADOS REAIS do
# sistema: módulos com progresso de horas, estado, avaliações
# e alterações ao cronograma.
#
# Autoria: base criada pelo Marcelo (dashboard Flask + export
# PDF). Evoluída no Bloco 3: deixou de usar dados mock (um
# horário fictício com salas/blocos de hora) e passou a ler do
# GestorCronograma — o mesmo domínio que o terminal (main.py)
# gere. "Uma lógica Python, vários canais" (ver 2.5).
#
# O dashboard é o "cockpit interno" do coordenador (camada 5).
# Lê os ficheiros JSON em dados/ (a fonte de verdade local);
# o Google Sheets continua a ser alvo de sincronização/publicação,
# não a fonte do dashboard.
#
# Executar com: python app.py  ->  http://127.0.0.1:5000
# Dependências: Flask, reportlab
# ============================================================

import json
import os
import tempfile
import time
from functools import wraps
from io import BytesIO, StringIO

from flask import (
    Flask,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from classes.auditoria import RegistoAuditoria, registo_from_dict
from classes.autenticacao import GestorAutenticacao
from classes.brevo_sender import BrevoSender
from classes.carregador_sheets import gestor_a_partir_de_sheets
from classes.email_sender import EmailSender
from classes.gerador_ics import gerar_ics
from classes.gerador_qr import gerar_qr_bytes
from classes.google_sheets import GoogleSheetsSync
from classes.importador_csv import ImportadorCSV
from classes.insights_engine import InsightsEngine
from classes.token_modulo import criar_token_modulo, validar_token_modulo
from gestor_cronograma import GestorCronograma

app = Flask(__name__)

# A secret_key é usada pelo Flask para assinar os "cookies" de sessão
# (é o que mantém o aluno autenticado entre páginas). Em produção (quando
# o site estiver alojado) deve vir de uma variável de ambiente secreta;
# localmente usamos um valor de desenvolvimento. NUNCA pôr a chave real
# no código que vai para o GitHub.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-local-mudar-em-producao")


# ------------------------------------------------------------
# Fonte de dados do dashboard (Fase B)
# ------------------------------------------------------------
# FONTE_DADOS decide DE ONDE o dashboard lê:
#   - "json"   (por defeito) -> ficheiros locais dados/*.json
#                               (é o que se usa em desenvolvimento,
#                               no PC do coordenador)
#   - "sheets" -> reconstrói o gestor a partir do Google Sheet
#                 privado (é o que se usa quando o site está ALOJADO
#                 na internet, longe da pasta dados/ local)
# Define-se por variável de ambiente — não é preciso mexer no código
# para mudar de modo.
FONTE_DADOS = os.environ.get("FONTE_DADOS", "json")

# Pasta dos dados locais. Por defeito "dados"; pode ser mudada por
# variável de ambiente (útil para os testes correrem numa pasta
# temporária, sem tocar nos dados reais).
PASTA_DADOS = os.environ.get("PASTA_DADOS", "dados")

# Cache simples para o modo "sheets": evita ir ao Google em CADA pedido
# (cada leitura do Sheet custa tempo e conta para os limites da API).
# Guardamos o gestor e a hora; reutilizamos durante alguns segundos.
_cache_sheets = {"gestor": None, "hora": 0.0}
_CACHE_SEGUNDOS = 30


def carregar_gestor_do_sheets():
    """
    Reconstrói o gestor a partir do Google Sheet privado.

    As credenciais e o ID da spreadsheet vêm de variáveis de ambiente
    (no alojamento são segredos da plataforma; nunca ficam no código):
      - GOOGLE_SHEETS_CREDENCIAIS: caminho do credentials.json
      - GOOGLE_SHEETS_NOME: ID (ou nome) da spreadsheet

    Se a ligação falhar, devolve um gestor vazio em vez de rebentar
    (graceful degradation, secção 5.3).

    Retorna:
        GestorCronograma: gestor reconstruído a partir do Sheet.
    """
    credenciais = os.environ.get("GOOGLE_SHEETS_CREDENCIAIS", "credentials.json")
    spreadsheet = os.environ.get("GOOGLE_SHEETS_NOME", "")

    gsheets = GoogleSheetsSync(credenciais, spreadsheet)
    gsheets.conectar()
    if not gsheets.conectado:
        return GestorCronograma(pasta_dados=PASTA_DADOS)

    return gestor_a_partir_de_sheets(gsheets)


def carregar_gestor():
    """
    Devolve um GestorCronograma com os dados frescos.

    Em modo "json" (local) lê os ficheiros dados/*.json — são pequenos,
    por isso recarregar a cada pedido é barato e mostra sempre o estado
    actual. Em modo "sheets" (alojado) lê do Google Sheet, com uma cache
    de poucos segundos para não martelar a API.

    Retorna:
        GestorCronograma: gestor pronto a usar.
    """
    if FONTE_DADOS == "sheets":
        agora = time.time()
        if (_cache_sheets["gestor"] is not None
                and (agora - _cache_sheets["hora"]) < _CACHE_SEGUNDOS):
            return _cache_sheets["gestor"]

        gestor = carregar_gestor_do_sheets()
        _cache_sheets["gestor"] = gestor
        _cache_sheets["hora"] = agora
        return gestor

    gestor = GestorCronograma(pasta_dados=PASTA_DADOS)
    gestor.carregar_dados()
    return gestor


def _invalidar_cache_sheets():
    """Esquece o gestor em cache, para a próxima leitura vir fresca do Sheet."""
    _cache_sheets["gestor"] = None
    _cache_sheets["hora"] = 0.0


def gestor_para_escrita():
    """
    Devolve (gestor, gsheets) prontos para uma operação de ESCRITA da admin.

    A escrita é diferente da leitura: não pode usar a cache (precisa do
    estado mais fresco) e, no alojamento, tem de saber gravar de volta.

      - Modo "sheets" (alojado): reconstrói um gestor fresco a partir do
        Sheet e devolve também a ligação `gsheets`, para quem chama poder
        sincronizar de volta SÓ a tab afectada (escrita cirúrgica — nunca
        uma sincronização total, que apagaria a tab dos Professores, que o
        reconstrutor não carrega).
      - Modo "json" (local): devolve o gestor dos ficheiros locais e
        gsheets=None (os métodos do gestor já gravam o JSON sozinhos).

    Retorna:
        (GestorCronograma, GoogleSheetsSync|None): o gestor e, se alojado,
        a ligação ao Sheet. (None, None) se o Sheet não estiver acessível.
    """
    if FONTE_DADOS == "sheets":
        credenciais = os.environ.get("GOOGLE_SHEETS_CREDENCIAIS", "credentials.json")
        spreadsheet = os.environ.get("GOOGLE_SHEETS_NOME", "")
        gsheets = GoogleSheetsSync(credenciais, spreadsheet)
        gsheets.conectar()
        if not gsheets.conectado:
            return None, None
        return gestor_a_partir_de_sheets(gsheets), gsheets

    gestor = GestorCronograma(pasta_dados=PASTA_DADOS)
    gestor.carregar_dados()
    return gestor, None


def carregar_auth():
    """
    Cria um GestorAutenticacao com as contas frescas.

    Em modo "sheets" (alojado), as contas vivem na tab "Utilizadores"
    do Google Sheet — assim sobrevivem a reinícios/redeploys do host
    (cujo disco pode ser efémero). Em modo "json" (local), usa o
    ficheiro dados/utilizadores.json.

    É chamado por pedido para que um registo seja imediatamente visível
    no login seguinte.

    Retorna:
        GestorAutenticacao: já com as contas carregadas.
    """
    if FONTE_DADOS == "sheets":
        credenciais = os.environ.get("GOOGLE_SHEETS_CREDENCIAIS", "credentials.json")
        spreadsheet = os.environ.get("GOOGLE_SHEETS_NOME", "")
        gsheets = GoogleSheetsSync(credenciais, spreadsheet)
        gsheets.conectar()
        if gsheets.conectado:
            return GestorAutenticacao(gsheets=gsheets, secret=app.secret_key)
        # Se a ligação falhar, cai para o ficheiro local (degradação graciosa)

    return GestorAutenticacao(
        caminho=os.path.join(PASTA_DADOS, "utilizadores.json"),
        secret=app.secret_key,
    )


def _ler_chaves_do_env(caminho, valores):
    """
    Preenche as chaves indicadas a partir de um ficheiro .env.

    Lê o ficheiro linha a linha (formato CHAVE=VALOR) e só preenche as
    chaves (do dicionário `valores`) que ainda estão vazias — assim o
    ambiente tem prioridade sobre o ficheiro. Se o ficheiro não existir,
    devolve os valores tal como vieram.

    Parâmetros:
        caminho (str): Caminho do ficheiro .env.
        valores (dict): Dicionário com as chaves a preencher (algumas vazias).

    Retorna:
        dict: O mesmo dicionário, com as chaves em falta preenchidas.
    """
    try:
        ficheiro = open(caminho, "r", encoding="utf-8")
        linhas = ficheiro.readlines()
        ficheiro.close()
    except FileNotFoundError:
        return valores

    for linha in linhas:
        linha = linha.strip()
        if linha == "" or linha[0] == "#" or "=" not in linha:
            continue
        posicao = linha.find("=")
        chave = linha[:posicao].strip()
        valor = linha[posicao + 1:].strip()
        if chave in valores and valores[chave] == "":
            valores[chave] = valor

    return valores


def carregar_email():
    """
    Devolve um "sender" de email pronto a usar — Brevo OU Gmail/SMTP.

    Escolhe sozinho o melhor canal disponível:
      1. **Brevo (API por HTTP)** — se houver BREVO_API_KEY. É o que funciona
         no ALOJAMENTO (Render), porque envia por HTTPS e não por SMTP (que o
         Render bloqueia no plano gratuito). Precisa só da chave + remetente.
      2. **Gmail/SMTP (EmailSender)** — caso contrário. É o que se usa no PC
         do coordenador e no terminal, onde o SMTP não está bloqueado.

    As credenciais vêm das variáveis de ambiente (alojamento) e, em falta,
    do ficheiro .env local (desenvolvimento). Os dois "senders" têm a mesma
    interface (.configurado + .enviar(...)), por isso quem chama não precisa
    de saber qual está a ser usado.

    Retorna:
        BrevoSender ou EmailSender: configurado se houver credenciais; senão,
        um EmailSender "vazio" (configurado == False) — quem chama trata disso.
    """
    valores = {
        "EMAIL_REMETENTE": os.environ.get("EMAIL_REMETENTE", ""),
        "EMAIL_PASSWORD": os.environ.get("EMAIL_PASSWORD", ""),
        "EMAIL_SERVIDOR": os.environ.get("EMAIL_SERVIDOR", ""),
        "EMAIL_PORTA": os.environ.get("EMAIL_PORTA", ""),
        "BREVO_API_KEY": os.environ.get("BREVO_API_KEY", ""),
    }
    # Completar do .env local o que faltar (no Render não há .env -> no-op).
    valores = _ler_chaves_do_env(".env", valores)

    remetente = valores["EMAIL_REMETENTE"]

    # 1) Preferir o Brevo (HTTP) — é o canal que funciona no alojamento.
    if valores["BREVO_API_KEY"] != "" and remetente != "":
        brevo = BrevoSender()
        brevo.configurar(valores["BREVO_API_KEY"], remetente, "Cronograma FORAVE")
        return brevo

    # 2) Senão, Gmail/SMTP (PC do coordenador, terminal).
    sender = EmailSender()
    password = valores["EMAIL_PASSWORD"]
    if remetente == "" or password == "":
        return sender  # fica por configurar (configurado == False)

    # Assume Gmail por defeito; só troca servidor/porta se forem indicados.
    sender.configurar_gmail(remetente, password)
    if valores["EMAIL_SERVIDOR"] != "":
        sender.servidor = valores["EMAIL_SERVIDOR"]
    if valores["EMAIL_PORTA"] != "":
        try:
            sender.porta = int(valores["EMAIL_PORTA"])
        except ValueError:
            sender.porta = 587  # valor inválido -> assume a porta padrão

    return sender


def utilizador_actual():
    """
    Devolve o email do utilizador autenticado, ou None.

    A sessão do Flask guarda o email após o login. Se não houver
    ninguém autenticado, a chave "email" não existe e devolve None.
    """
    return session.get("email", None)


# ------------------------------------------------------------
# Coordenador — quem tem direitos de administração
# ------------------------------------------------------------
# Os direitos de coordenador NÃO se ganham pelo registo (senão qualquer
# um se promovia). São atribuídos por uma lista de emails de confiança,
# definida fora do código: a variável COORDENADOR_EMAILS (no ambiente do
# alojamento, ou no .env local). Quem estiver nessa lista entra como
# coordenador; todos os outros são alunos. É simples e à prova de abusos.

def _config(chave, default=""):
    """
    Lê uma variável de configuração do ambiente ou, em falta, do .env local.

    Parâmetros:
        chave (str): Nome da variável (ex: "COORDENADOR_EMAILS").
        default (str): Valor a devolver se não existir em lado nenhum.

    Retorna:
        str: O valor encontrado, ou o default.
    """
    valor = os.environ.get(chave, "")
    if valor == "":
        valor = _ler_chaves_do_env(".env", {chave: ""}).get(chave, "")
    if valor == "":
        return default
    return valor


def emails_coordenador():
    """
    Devolve o conjunto de emails autorizados como coordenador.

    Lê COORDENADOR_EMAILS (emails separados por vírgula) e devolve-os em
    minúsculas, para a comparação ser indiferente a maiúsculas.

    Retorna:
        set: Emails de coordenador (em minúsculas). Vazio se não definido.
    """
    bruto = _config("COORDENADOR_EMAILS", "")
    autorizados = set()
    for email in bruto.split(","):
        email = email.strip().lower()
        if email != "":
            autorizados.add(email)
    return autorizados


def papel_do_email(email, papel_guardado="aluno", gestor=None):
    """
    Decide o papel efectivo de um email (autorização por papéis).

    Prioridade:
      1. "coordenador" — se o email estiver em COORDENADOR_EMAILS (lista de
         confiança); vê e gere TODOS os módulos.
      2. "professor"   — se o email pertencer a um professor do sistema
         (precisa do gestor para o descobrir); gere SÓ o(s) seu(s) módulo(s).
      3. papel_guardado (por defeito "aluno").

    Parâmetros:
        email (str): Email do utilizador.
        papel_guardado (str): Papel vindo da conta (Sheet/JSON).
        gestor (GestorCronograma): opcional; se dado, permite detectar o
                                   papel "professor" (email -> professor).

    Retorna:
        str: "coordenador", "professor" ou "aluno".
    """
    if email.lower() in emails_coordenador():
        return "coordenador"
    if gestor is not None and gestor.procurar_professor_por_email(email) is not None:
        return "professor"
    return papel_guardado


def modulos_geridos(gestor):
    """
    Nomes dos módulos que o utilizador em sessão pode gerir na admin.

    - Coordenador -> None (sinal de "todos", sem filtro).
    - Professor   -> conjunto com os nomes dos SEUS módulos (os que têm o
                     nome dele no campo 'professor' do módulo, ou que estão
                     na sua lista de módulos). Vazio se não tiver nenhum.
    - Outros      -> conjunto vazio (não gere nada).

    Recalcula-se por pedido a partir dos dados frescos (não fica preso na
    sessão), para a autorização acompanhar mudanças nos dados.
    """
    if session.get("papel") == "coordenador":
        return None  # todos

    prof = gestor.procurar_professor_por_email(session.get("email", ""))
    if prof is None:
        return set()

    nomes = set()
    for m in gestor.modulos:
        # Defensivo: só casar por nome se o professor tiver nome (evita que um
        # registo com nome vazio "apanhe" módulos com o campo professor vazio).
        casa_por_nome = prof.nome != "" and m.professor == prof.nome
        if casa_por_nome or m.nome in prof.modulos:
            nomes.add(m.nome)
    return nomes


def pode_gerir_modulo(gestor, nome_modulo):
    """
    Autoriza uma ESCRITA sobre um módulo específico.

    True se o utilizador é coordenador (gere tudo) ou se o módulo está
    entre os que gere (professor do próprio módulo). É a barreira que
    impede um professor de mexer no módulo de outro.
    """
    geridos = modulos_geridos(gestor)
    return geridos is None or nome_modulo in geridos


def apenas_coordenador(funcao):
    """
    Protege uma rota reservada ao COORDENADOR (ex: criar/importar módulos).

    Se a sessão não for de coordenador, encaminha para o login. É a
    concretização da AUTORIZAÇÃO (ter permissão), por oposição à
    autenticação (estar identificado).
    """
    @wraps(funcao)
    def protegida(*args, **kwargs):
        if session.get("papel") != "coordenador":
            flash("Acesso reservado ao coordenador. Inicia sessão.", "erro")
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return protegida


def apenas_staff(funcao):
    """
    Protege a área de gestão: passa se for COORDENADOR ou PROFESSOR.

    O coordenador vê tudo; o professor vê só os seus módulos (o âmbito é
    aplicado dentro de cada rota, via modulos_geridos/pode_gerir_modulo).
    """
    @wraps(funcao)
    def protegida(*args, **kwargs):
        if session.get("papel") not in ("coordenador", "professor"):
            flash("Acesso reservado a coordenadores e professores. Inicia sessão.", "erro")
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return protegida


def login_obrigatorio(funcao):
    """
    Protege uma rota: exige sessão iniciada (qualquer papel).

    Usado no cronograma e nas APIs de dados: os dados do curso deixaram de
    ser públicos (RGPD) — a página inicial passou a ser uma landing e tudo
    o que mostra dados exige identificação.
    """
    @wraps(funcao)
    def protegida(*args, **kwargs):
        if utilizador_actual() is None:
            flash("Inicia sessão para continuares.", "erro")
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return protegida


def dados_aluno(gestor, email):
    """
    Reúne os dados que um aluno pode ver de si próprio.

    Para o email indicado, devolve um dicionário com o nome e a lista
    dos módulos em que está inscrito — cada um com o progresso, a nota
    final (UFCD) calculada, e as avaliações com a nota dele em cada uma.

    RGPD: só inclui dados DESTE aluno. As notas de outros alunos nunca
    entram aqui — é por isso que a área é autenticada.

    Parâmetros:
        gestor (GestorCronograma): fonte dos dados.
        email (str): email do aluno autenticado (chave única).

    Retorna:
        dict: {"email", "nome", "modulos": [...]}.
    """
    # Encontrar o formando pelo email (padrão for + if)
    formando = None
    for f in gestor.formandos:
        if f.email == email:
            formando = f

    if formando is None:
        # Tem conta mas já não está na lista de formandos (ex: removido)
        return {"email": email, "nome": email, "modulos": [], "eventos": []}

    modulos_aluno = []
    # Eventos para o calendário visual (aulas + avaliações dos módulos do aluno).
    # Cada evento leva a data (dd/mm/aaaa) e o tipo, para o JS os desenhar.
    eventos = []
    for m in gestor.modulos:
        # Só os módulos em que este aluno está inscrito
        if not formando.esta_inscrito(m.nome):
            continue

        # Avaliações com a nota DESTE aluno (None se ainda não lançada)
        avaliacoes = []
        for av in m.avaliacoes:
            dados_av = {}
            dados_av["data"] = av.data
            dados_av["tipo"] = av.tipo
            dados_av["descricao"] = av.descricao
            dados_av["peso"] = av.peso
            dados_av["nota"] = av.obter_nota(email)
            avaliacoes.append(dados_av)
            # Evento de avaliação (só se tiver dia marcado)
            if av.data:
                eventos.append({
                    "data": av.data,
                    "tipo": "avaliacao",
                    "titulo": av.descricao or av.tipo or "Avaliação",
                    "modulo": m.nome,
                })

        # Eventos das aulas (cada sessão do cronograma com data)
        for s in m.sessoes:
            if s.get("data"):
                eventos.append({
                    "data": s["data"],
                    "tipo": "aula",
                    "titulo": m.nome,
                    "modulo": m.nome,
                    "horas": s.get("horas", 0),
                    "realizada": bool(s.get("realizada")),
                })

        dados_m = {}
        dados_m["nome"] = m.nome
        dados_m["ufcd"] = m.ufcd
        dados_m["professor"] = m.professor
        dados_m["estado"] = m.estado
        dados_m["percentagem"] = round(m.percentagem_concluida(), 1)
        dados_m["nota_final"] = m.nota_final(email)
        dados_m["avaliacoes"] = avaliacoes
        modulos_aluno.append(dados_m)

    return {"email": email, "nome": formando.nome,
            "modulos": modulos_aluno, "eventos": eventos}


@app.route('/')
def landing():
    """
    Página inicial PÚBLICA — só boas-vindas + opções de entrada por perfil.

    NÃO mostra dados do curso (módulos, notas, nomes): é a "montra" do
    sistema. Os dados do curso vivem no /cronograma e nas áreas por papel,
    todos atrás de login (decisão RGPD — o público não vê dados internos).
    """
    return render_template('landing.html')


@app.route('/cronograma')
@login_obrigatorio
def cronograma():
    """
    Cronograma (módulos, progresso, gráfico, PDF) — só para autenticados.

    Era a antiga página inicial pública; passou para trás de login para não
    expor dados do curso a visitantes anónimos. Acessível a qualquer perfil.
    """
    return render_template('dashboard.html')


@app.route('/cronograma.ics')
def cronograma_ics():
    """
    Exporta o cronograma completo (aulas) em iCalendar (.ics). PÚBLICO.

    Cada data de aula de cada módulo vira um evento de dia inteiro. Qualquer
    pessoa descarrega o ficheiro e importa-o no Google Calendar/Outlook/
    telemóvel, ficando com as aulas e os lembretes nativos.

    Decisão de dados (03/Jul): o HORÁRIO das aulas é informação pública (como
    o nome do curso, a UFCD e o professor, já visíveis na landing) — não são
    dados pessoais de ninguém. Por isso este canal é aberto, e alimenta a
    secção "Adicionar ao calendário" da landing (botão + QR). As NOTAS, essas
    sim pessoais, continuam sempre atrás de login.
    """
    gestor = carregar_gestor()
    conteudo = gerar_ics(gestor.modulos)
    return Response(
        conteudo,
        mimetype='text/calendar',
        headers={'Content-Disposition': 'attachment; filename="cronograma-forave.ics"'},
    )


def _slug_ficheiro(texto):
    """
    Constrói um nome de ficheiro seguro (ASCII, sem espaços) a partir do
    nome do módulo. Ex.: "Python Avançado" -> "Python-Avanado". Serve só
    para o nome do .ics descarregado; a identidade real do módulo continua
    a ser o nome completo.
    """
    seguro = ""
    for caracter in texto:
        if caracter.isascii() and caracter.isalnum():
            seguro = seguro + caracter
        elif caracter in (" ", "-", "_"):
            seguro = seguro + "-"
    seguro = seguro.strip("-")
    if seguro == "":
        seguro = "modulo"
    return seguro


@app.route('/modulo.ics')
def modulo_ics():
    """
    Exporta o .ics de UM módulo (as suas datas de aula).

    Aceita duas formas de entrada, para servir os dois cenários do QR/botão:
      - ?t=<token>  -> token assinado (o QR de cada módulo usa isto). Funciona
                       sem sessão iniciada, para a câmara do telemóvel poder
                       abrir o link directamente. O token expira (30 dias) e
                       não é falsificável (assinado com a chave da app).
      - ?nome=<nome> -> pela sessão iniciada (o botão dentro do dashboard).
                        Exige login, como o resto dos dados do curso (RGPD).

    Em ambos os casos o .ics resultante são só datas de aulas (não são dados
    pessoais de ninguém) — é mais um canal da mesma lógica de domínio.
    """
    token = request.args.get('t', '')
    if token:
        nome = validar_token_modulo(token, app.secret_key)
        if nome is None:
            abort(403)  # token corrompido, falsificado ou expirado
    else:
        # Sem token -> tem de haver sessão (mesma regra RGPD do cronograma)
        if utilizador_actual() is None:
            flash("Inicia sessão para continuares.", "erro")
            return redirect(url_for("login"))
        nome = request.args.get('nome', '')

    gestor = carregar_gestor()
    modulo = gestor.procurar_modulo(nome)
    if modulo is None:
        abort(404)

    conteudo = gerar_ics([modulo])
    nome_ficheiro = _slug_ficheiro(nome) + ".ics"
    return Response(
        conteudo,
        mimetype='text/calendar',
        headers={'Content-Disposition': f'attachment; filename="{nome_ficheiro}"'},
    )


@app.route('/modulo/qr.png')
@login_obrigatorio
def modulo_qr():
    """
    Serve o QR code (PNG) de um módulo. O QR é MOSTRADO só a quem já está
    autenticado no dashboard, mas o link que ele contém leva um token
    assinado — assim, quando alguém aponta a câmara do telemóvel, o /modulo.ics
    abre sem pedir login (ver modulo_ics). O PNG é gerado em memória.
    """
    nome = request.args.get('nome', '')
    gestor = carregar_gestor()
    if gestor.procurar_modulo(nome) is None:
        abort(404)

    token = criar_token_modulo(nome, app.secret_key)
    url = url_for('modulo_ics', t=token, _external=True)
    return Response(gerar_qr_bytes(url), mimetype='image/png')


@app.route('/qr-cronograma.png')
def qr_cronograma():
    """
    Serve um QR code (PNG) que aponta para o /cronograma.ics PÚBLICO.

    É a ponte ecrã→telemóvel do cronograma completo: quem aponta a câmara
    (a partir da landing num portátil, de um cartaz ou de um slide) recebe
    logo TODAS as aulas no calendário do telemóvel. Não expõe dados pessoais
    (só datas de aulas — ver cronograma_ics). O PNG é gerado em memória.
    """
    url = url_for('cronograma_ics', _external=True)
    return Response(gerar_qr_bytes(url), mimetype='image/png')


@app.route('/qr-login.png')
def qr_login():
    """
    Serve um QR code (PNG) que aponta para a PÁGINA DE LOGIN.

    NÃO é usado na landing (aí seria redundante — quem está na página carrega
    no botão "Entrar"). Existe para poder ser impresso num CARTAZ no corredor
    ou posto num SLIDE da defesa: nesses meios não-clicáveis, o QR é a ponte
    para o telemóvel. Não expõe dados — cai no ecrã de entrada.
    """
    url = url_for('login', _external=True)
    return Response(gerar_qr_bytes(url), mimetype='image/png')


@app.route('/sw.js')
def service_worker():
    """
    Serve o service worker a partir da RAIZ do site.

    Um service worker só controla as páginas que estão "abaixo" do
    sítio onde ele próprio é servido (o seu "scope"). Servindo-o em
    /sw.js (raiz), ele controla todo o site — o que é preciso para
    o PWA funcionar em todas as páginas. (Bloco 4 / Fase D)
    """
    caminho = os.path.join(app.root_path, 'static', 'sw.js')
    return send_file(caminho, mimetype='application/javascript')


# ============================================================
# AUTENTICAÇÃO — registo, login, logout e área do aluno
# ============================================================

@app.route('/registar', methods=['GET', 'POST'])
def registar():
    """
    Auto-registo do aluno.

    Regras (validadas no POST):
      - email e password preenchidos
      - as duas passwords coincidem
      - password com pelo menos 6 caracteres
      - o email TEM de estar na lista de formandos do curso
        (é o que impede que estranhos criem conta)
      - ainda não existe conta com esse email
    """
    # Perfil (aluno/coordenador) só para a página manter o aspecto certo; vem
    # na query string, disponível em request.args mesmo num POST.
    perfil = request.args.get('perfil', '')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        gestor = carregar_gestor()
        auth = carregar_auth()

        if email == '' or password == '':
            flash('Preenche o email e a password.', 'erro')
            return redirect(url_for('registar', perfil=perfil))

        if password != password2:
            flash('As duas passwords não coincidem.', 'erro')
            return redirect(url_for('registar', perfil=perfil))

        if len(password) < 6:
            flash('A password deve ter pelo menos 6 caracteres.', 'erro')
            return redirect(url_for('registar', perfil=perfil))

        # Pode registar-se quem for formando do curso, um professor do curso,
        # OU um email de coordenador (que normalmente não está nas listas).
        if (not gestor.formando_existe(email)
                and not gestor.professor_existe(email)
                and email.lower() not in emails_coordenador()):
            flash('Esse email não está na lista de formandos nem de professores do curso. '
                  'Confirma que usaste o teu email @forave ou fala com o coordenador.', 'erro')
            return redirect(url_for('registar', perfil=perfil))

        if auth.email_registado(email):
            flash('Já existe uma conta com esse email. Faz login.', 'erro')
            return redirect(url_for('login', perfil=perfil))

        auth.registar(email, password)
        flash('Conta criada com sucesso! Já podes entrar.', 'ok')
        return redirect(url_for('login', perfil=perfil))

    return render_template('registar.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login do aluno. Em caso de sucesso, guarda o email na sessão
    e encaminha para a área pessoal.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        auth = carregar_auth()
        utilizador = auth.autenticar(email, password)

        if utilizador is None:
            flash('Email ou password incorrectos.', 'erro')
            # Preserva o perfil (aluno/coordenador) para a página manter o
            # mesmo aspecto após um erro. O perfil vem na query string, que o
            # Flask disponibiliza em request.args mesmo num POST.
            return redirect(url_for('login', perfil=request.args.get('perfil', '')))

        # Papel efectivo: coordenador (lista COORDENADOR_EMAILS) > professor
        # (email pertence a um professor dos dados) > o que estiver guardado.
        gestor = carregar_gestor()
        papel = papel_do_email(utilizador.email, utilizador.papel, gestor)
        session['email'] = utilizador.email
        session['papel'] = papel

        # Staff (coordenador/professor) entra na gestão; aluno, nas suas notas.
        if papel in ('coordenador', 'professor'):
            return redirect(url_for('admin'))
        return redirect(url_for('area_aluno'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Termina a sessão e volta à página inicial (landing)."""
    session.clear()
    return redirect(url_for('landing'))


@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    """
    Pedido de reposição de password ("esqueci-me da password").

    O aluno escreve o email; se existir conta, geramos um token assinado
    e enviamos um link de reposição por email. A resposta ao utilizador é
    SEMPRE a mesma mensagem neutra — quer o email exista, quer não — para
    não revelar quem tem conta (boa prática de segurança).
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        auth = carregar_auth()
        token = auth.criar_token_reposicao(email)

        # Só há email para enviar se a conta existir (token != None).
        if token is not None:
            link = url_for('repor_password', token=token, _external=True)
            # O envio de email NUNCA pode partir esta página: se falhar (ex.:
            # alojamento gratuito que bloqueia o SMTP de saída), apanhamos o
            # erro e registamos o link no log para o coordenador poder ajudar.
            try:
                sender = carregar_email()
                enviado = False
                if sender.configurado:
                    corpo = (
                        "Olá,\n\n"
                        "Recebemos um pedido para repor a password da tua conta no "
                        "Cronograma FORAVE.\n\n"
                        "Abre este link para definir uma nova password (válido 1 hora):\n"
                        f"{link}\n\n"
                        "Se não foste tu a pedir, ignora este email — a tua password "
                        "actual continua válida.\n\n"
                        "Cronograma FORAVE"
                    )
                    enviado = sender.enviar(
                        email, email, "Repor password — Cronograma FORAVE", corpo
                    )
                if not enviado:
                    # Email por configurar ou envio falhou: deixar o link no log.
                    print(f"[RECUPERAR] Email não enviado — link para {email}: {link}")
            except Exception as erro:
                print(f"[RECUPERAR] Erro ao enviar email para {email}: {erro}")
                print(f"[RECUPERAR] Link (fallback no log): {link}")

        flash('Se esse email tiver uma conta, enviámos um link de reposição. '
              'Verifica a tua caixa de correio (e o spam).', 'ok')
        return redirect(url_for('login'))

    return render_template('recuperar.html')


@app.route('/repor/<token>', methods=['GET', 'POST'])
def repor_password(token):
    """
    Definição da nova password, a partir do link enviado por email.

    Valida o token (assinatura + validade + uso único). Se for válido,
    mostra o formulário (GET) e grava a nova password (POST).
    """
    auth = carregar_auth()
    email = auth.validar_token_reposicao(token)

    if email is None:
        flash('Esse link de reposição é inválido ou expirou. Pede um novo.', 'erro')
        return redirect(url_for('recuperar'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if password == '':
            flash('Escreve a nova password.', 'erro')
            return redirect(request.url)

        if password != password2:
            flash('As duas passwords não coincidem.', 'erro')
            return redirect(request.url)

        if len(password) < 6:
            flash('A password deve ter pelo menos 6 caracteres.', 'erro')
            return redirect(request.url)

        auth.redefinir_password(email, password)
        flash('Password actualizada com sucesso! Já podes entrar.', 'ok')
        return redirect(url_for('login'))

    return render_template('repor.html', token=token, email=email)


@app.route('/aluno')
def area_aluno():
    """
    Área pessoal do aluno — só acessível autenticado.

    Se não houver sessão, encaminha para o login. Mostra apenas
    os dados do próprio aluno (notas e nota final por UFCD).
    """
    email = utilizador_actual()
    if email is None:
        flash('Inicia sessão para veres as tuas notas.', 'erro')
        return redirect(url_for('login'))

    gestor = carregar_gestor()
    aluno = dados_aluno(gestor, email)
    return render_template('aluno.html', aluno=aluno)


# ============================================================
# ADMINISTRAÇÃO (coordenador) — ver tudo + gerir módulos/notas
# ============================================================
# Área reservada ao coordenador (protegida por @apenas_coordenador).
# Mostra o que o público não vê (todas as notas de todos os alunos) e
# permite gerir módulos, avaliações e notas a partir do site.
#
# ESCRITA (Fase 2): quando o site está alojado (modo "sheets"), cada
# alteração é sincronizada SÓ para a tab afectada (cirúrgico) e a cache
# é invalidada para a mudança aparecer logo. Nunca se faz sincronização
# total — apagaria a tab dos Professores (que o reconstrutor não carrega).
#
# AUDITORIA (accountability): como o RBAC é tudo-ou-nada (qualquer
# coordenador pode editar tudo), cada ESCRITA da admin deixa um registo
# "quem fez o quê e quando" — append-only, para se poder responder mais
# tarde a "quem lançou/alterou esta nota?". Ver classes/auditoria.py.


def _caminho_auditoria():
    """Caminho do ficheiro de auditoria local (modo json)."""
    return os.path.join(PASTA_DADOS, "auditoria.json")


def registar_auditoria(gsheets, accao, detalhe):
    """
    Regista uma entrada de auditoria (quem fez o quê e quando).

    Append-only e ROBUSTO: se o registo falhar, NUNCA parte a operação
    que o chamou (só avisa no log) — o pior caso é ficarmos sem uma
    linha de auditoria, nunca sem a acção em si.

    Persistência (espelha a das outras entidades):
      - Modo alojado (gsheets != None): acrescenta à tab "Auditoria".
        Reutiliza a ligação que a rota já abriu (gestor_para_escrita).
      - Modo local (gsheets == None): acrescenta a dados/auditoria.json.

    Parâmetros:
        gsheets (GoogleSheetsSync|None): ligação ao Sheet, ou None (local).
        accao (str): tipo de acção (ex: "Lançar notas").
        detalhe (str): descrição legível do que mudou.
    """
    autor = utilizador_actual() or "coordenador"
    registo = RegistoAuditoria(autor=autor, accao=accao, detalhe=detalhe)
    try:
        if gsheets is not None:
            gsheets.acrescentar_auditoria(
                registo.data_hora, registo.autor, registo.accao, registo.detalhe
            )
        else:
            caminho = _caminho_auditoria()
            registos = []
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    registos = json.load(f)
            registos.append(registo.to_dict())
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(registos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Auditoria é secundária à acção — nunca deve rebentar a página.
        print(f"  [AVISO] Auditoria não registada ({accao}): {e}")


def ler_auditoria(limite=30):
    """
    Lê as entradas de auditoria mais recentes (para mostrar na admin).

    Decide sozinha a fonte (como carregar_auth): no modo alojado lê da
    tab "Auditoria"; no modo local, de dados/auditoria.json. Devolve no
    máximo `limite` entradas, das mais recentes para as mais antigas.
    Nunca parte a página: em caso de erro devolve lista vazia.

    Retorna:
        list: dicts {data_hora, autor, accao, detalhe}, recentes primeiro.
    """
    try:
        if FONTE_DADOS == "sheets":
            credenciais = os.environ.get("GOOGLE_SHEETS_CREDENCIAIS", "credentials.json")
            spreadsheet = os.environ.get("GOOGLE_SHEETS_NOME", "")
            gs = GoogleSheetsSync(credenciais, spreadsheet)
            gs.conectar()
            brutos = gs.obter_auditoria() if gs.conectado else []
        else:
            caminho = _caminho_auditoria()
            if not os.path.exists(caminho):
                return []
            with open(caminho, "r", encoding="utf-8") as f:
                brutos = json.load(f)

        # Normaliza pela classe (tolerante a chaves em falta) e ordena
        registos = [registo_from_dict(d).to_dict() for d in brutos]
        registos.reverse()  # mais recentes primeiro
        if limite is None:     # None -> devolve TUDO (usado no download CSV)
            return registos
        return registos[:limite]
    except Exception as e:
        print(f"  [AVISO] Não foi possível ler a auditoria: {e}")
        return []


def dados_admin(gestor, nomes_permitidos=None):
    """
    Reúne a visão de gestão dos módulos.

    Para cada módulo, junta as avaliações e a grelha de notas de TODOS os
    alunos inscritos (nota por avaliação + nota final). Inclui ainda a
    lista de formandos. É a visão "tudo à vista" que o público não tem.

    Parâmetros:
        gestor (GestorCronograma): fonte dos dados.
        nomes_permitidos (set|None): se for um conjunto, mostra só os
            módulos com esses nomes (âmbito do professor); None = todos
            (coordenador).

    Retorna:
        dict: {"modulos": [...], "formandos": [...]}.
    """
    modulos = []
    # Eventos para o calendário de overview do staff (aulas + avaliações dos
    # módulos que este utilizador vê — já filtrados pelo âmbito acima).
    eventos = []
    for m in gestor.modulos:
        # Âmbito por papel: o professor só vê os seus módulos
        if nomes_permitidos is not None and m.nome not in nomes_permitidos:
            continue
        # Avaliações do módulo (com índice — é o que o lançamento de notas usa)
        avaliacoes = []
        indice = 0
        for av in m.avaliacoes:
            avaliacoes.append({
                "indice": indice,
                "data": av.data,
                "tipo": av.tipo,
                "descricao": av.descricao,
                "objectivo": av.objectivo,
                "deliverables": av.deliverables,
                "peso": av.peso,
            })
            indice = indice + 1
            if av.data:
                eventos.append({"data": av.data, "tipo": "avaliacao",
                                "titulo": av.descricao or av.tipo or "Avaliação",
                                "modulo": m.nome})

        # Aulas (sessões com data) do módulo -> eventos do calendário
        for s in m.sessoes:
            if s.get("data"):
                eventos.append({"data": s["data"], "tipo": "aula",
                                "titulo": m.nome, "modulo": m.nome,
                                "horas": s.get("horas", 0),
                                "realizada": bool(s.get("realizada"))})

        # Alunos inscritos neste módulo, com a nota em cada avaliação
        alunos = []
        for f in gestor.formandos:
            if not f.esta_inscrito(m.nome):
                continue
            notas = []
            for av in m.avaliacoes:
                notas.append(av.obter_nota(f.email))
            alunos.append({
                "nome": f.nome,
                "email": f.email,
                "notas": notas,
                "nota_final": m.nota_final(f.email),
            })

        modulos.append({
            "nome": m.nome,
            "ufcd": m.ufcd,
            "professor": m.professor,
            "estado": m.estado,
            "horas_dadas": m.horas_dadas,
            "horas_totais": m.horas_totais,
            "percentagem": round(m.percentagem_concluida(), 1),
            "horas_restantes": m.horas_restantes(),
            "datas": m.datas,
            "sessoes": m.sessoes,
            "avaliacoes": avaliacoes,
            "alunos": alunos,
        })

    formandos = []
    for f in gestor.formandos:
        formandos.append({"nome": f.nome, "email": f.email, "modulos": f.modulos})

    # Professores (para a secção de gestão do coordenador). Lista completa —
    # não é filtrada pelo âmbito (só o coordenador vê esta secção).
    professores = []
    for p in gestor.professores:
        professores.append({"nome": p.nome, "email": p.email,
                            "telefone": p.telefone, "modulos": p.modulos})

    return {"modulos": modulos, "formandos": formandos,
            "professores": professores, "eventos": eventos}


@app.route('/admin')
@apenas_staff
def admin():
    """
    Painel de gestão. O coordenador vê todos os módulos; o professor vê só
    os seus (âmbito aplicado por modulos_geridos). Só leitura aqui — as
    escritas têm as suas próprias rotas.
    """
    gestor = carregar_gestor()
    geridos = modulos_geridos(gestor)          # None = todos (coordenador)
    dados = dados_admin(gestor, geridos)
    papel = session.get("papel")
    # O registo de alterações é uma visão de coordenação (e o detalhe das
    # notas de OUTROS módulos é dado pessoal) — só o coordenador o vê.
    auditoria = ler_auditoria(limite=50) if papel == "coordenador" else []
    return render_template('admin.html', dados=dados, auditoria=auditoria, papel=papel)


@app.route('/admin/auditoria.csv')
@apenas_coordenador
def admin_auditoria_csv():
    """
    Descarrega o registo de alterações COMPLETO em CSV (rastreabilidade).

    O ecrã mostra só as mais recentes; aqui exporta-se o histórico todo —
    arquivável e auditável fora do sistema. Só o coordenador acede.
    """
    import csv
    registos = ler_auditoria(limite=None)   # None -> tudo

    buffer = StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(["data_hora", "autor", "accao", "detalhe"])
    for e in registos:
        escritor.writerow([e.get("data_hora", ""), e.get("autor", ""),
                           e.get("accao", ""), e.get("detalhe", "")])

    # BOM (﻿) para o Excel abrir os acentos corretamente
    conteudo = "﻿" + buffer.getvalue()
    return Response(
        conteudo,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="registo_alteracoes.csv"'},
    )


@app.route('/admin/modulo', methods=['POST'])
@apenas_coordenador
def admin_adicionar_modulo():
    """Adiciona um módulo novo (escreve no backend activo)."""
    nome = request.form.get('nome', '').strip()
    professor = request.form.get('professor', '').strip()
    estado = request.form.get('estado', '').strip() or 'planeado'
    ufcd = request.form.get('ufcd', '').strip()
    datas = _texto_para_lista_form(request.form.get('datas', ''))

    if nome == '':
        flash('O módulo precisa de um nome.', 'erro')
        return redirect(url_for('admin'))

    horas_totais = _para_int_form(request.form.get('horas_totais', ''))
    horas_dadas = _para_int_form(request.form.get('horas_dadas', ''))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if gestor.modulo_existe(nome):
        flash(f'Já existe um módulo chamado "{nome}".', 'erro')
        return redirect(url_for('admin'))

    gestor.adicionar_modulo(nome, professor, horas_totais, horas_dadas, estado, datas, ufcd=ufcd)
    if gsheets is not None:
        gsheets.sincronizar_modulos(gestor.modulos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Adicionar módulo",
                       f'{nome} (UFCD {ufcd or "—"}, prof. {professor or "—"})')
    flash(f'Módulo "{nome}" adicionado.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/importar_csv', methods=['POST'])
@apenas_coordenador
def admin_importar_csv():
    """
    Importa módulos em massa a partir de um CSV enviado pela web.

    Permite carregar o cronograma inteiro de uma vez (colunas
    nome,professor,horas_totais,horas_dadas,estado + opcionais ufcd,datas —
    datas = dias de aula separados por ';'). Reusa o ImportadorCSV (o mesmo
    do terminal): grava o upload num ficheiro temporário e importa a partir
    dele. Duplicados (pelo nome) são saltados. Persistência cirúrgica na tab
    Módulos + registo de auditoria.
    """
    ficheiro = request.files.get('csv')
    if ficheiro is None or ficheiro.filename == '':
        flash('Escolhe um ficheiro CSV para importar.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    # Guardar o upload num ficheiro temporário e reusar o importador (que lê
    # de um caminho). O temporário é sempre apagado no fim (finally).
    fd, caminho = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        ficheiro.save(caminho)
        resumo = ImportadorCSV().importar_modulos(caminho, gestor)
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass

    # Persistir só se algo entrou (escrita cirúrgica na tab Módulos)
    if gsheets is not None and resumo['importados'] > 0:
        gsheets.sincronizar_modulos(gestor.modulos)
        _invalidar_cache_sheets()

    if resumo['importados'] > 0:
        registar_auditoria(gsheets, 'Importar CSV',
                           f"{resumo['importados']} módulo(s) importado(s), "
                           f"{resumo['saltados']} saltado(s), {resumo['erros']} erro(s)")

    categoria = 'ok' if resumo['erros'] == 0 else 'erro'
    flash(f"Importação: {resumo['importados']} importado(s), "
          f"{resumo['saltados']} já existiam, {resumo['erros']} erro(s).", categoria)
    return redirect(url_for('admin'))


def _processar_import_csv(importar_fn, sincronizar_fn, rotulo):
    """
    Fluxo comum de importação CSV pela web (formandos/professores).

    Faz o mesmo que o admin_importar_csv dos módulos — recebe o upload, grava-o
    num ficheiro temporário, chama o importador certo, sincroniza a tab afectada
    e regista auditoria — mas parametrizado, para não repetir o código.

    Parâmetros:
        importar_fn (callable): (caminho, gestor) -> resumo do ImportadorCSV.
        sincronizar_fn (callable): (gsheets, gestor) -> sincroniza a tab certa.
        rotulo (str): nome singular para as mensagens (ex.: "formando").
    """
    ficheiro = request.files.get('csv')
    if ficheiro is None or ficheiro.filename == '':
        flash('Escolhe um ficheiro CSV para importar.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    fd, caminho = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        ficheiro.save(caminho)
        resumo = importar_fn(caminho, gestor)
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass

    # Persistir só se algo entrou (escrita cirúrgica na tab afectada)
    if gsheets is not None and resumo['importados'] > 0:
        sincronizar_fn(gsheets, gestor)
        _invalidar_cache_sheets()

    if resumo['importados'] > 0:
        registar_auditoria(gsheets, 'Importar CSV',
                           f"{resumo['importados']} {rotulo}(s) importado(s), "
                           f"{resumo['saltados']} saltado(s), {resumo['erros']} erro(s)")

    categoria = 'ok' if resumo['erros'] == 0 else 'erro'
    flash(f"Importação: {resumo['importados']} importado(s), "
          f"{resumo['saltados']} já existiam, {resumo['erros']} erro(s).", categoria)
    return redirect(url_for('admin'))


@app.route('/admin/importar_csv_formandos', methods=['POST'])
@apenas_coordenador
def admin_importar_csv_formandos():
    """
    Importa formandos em massa a partir de um CSV (colunas nome,email,modulos —
    módulos separados por ';'). O motor (ImportadorCSV) já existia; esta rota
    liga-o à web, à imagem da importação de módulos. Duplicados (pelo email)
    são saltados.
    """
    return _processar_import_csv(
        lambda caminho, gestor: ImportadorCSV().importar_formandos(caminho, gestor),
        lambda gsheets, gestor: gsheets.sincronizar_formandos(gestor.formandos),
        'formando')


@app.route('/admin/importar_csv_professores', methods=['POST'])
@apenas_coordenador
def admin_importar_csv_professores():
    """
    Importa professores em massa a partir de um CSV (colunas
    nome,email,telefone,modulos — módulos separados por ';'). Liga o
    ImportadorCSV à web. Duplicados (pelo email) são saltados.
    """
    return _processar_import_csv(
        lambda caminho, gestor: ImportadorCSV().importar_professores(caminho, gestor),
        lambda gsheets, gestor: gsheets.sincronizar_professores(gestor.professores),
        'professor')


@app.route('/admin/professor', methods=['POST'])
@apenas_coordenador
def admin_adicionar_professor():
    """
    Cria um professor (com email) e associa-lhe módulos — pela web.

    É a peça que torna o papel "professor" utilizável sem o terminal: o
    coordenador dá um nome + email ao professor e escolhe que módulos ele
    gere. Depois esse email regista-se no site e passa a ver só esses
    módulos. Persistência cirúrgica na tab Professores + auditoria.
    """
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    telefone = request.form.get('telefone', '').strip()
    modulos = request.form.getlist('modulos')  # nomes dos módulos escolhidos

    if nome == '' or email == '':
        flash('O professor precisa de nome e email.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if gestor.professor_existe(email):
        flash(f'Já existe um professor com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    gestor.adicionar_professor(nome, email, telefone, modulos)
    if gsheets is not None:
        gsheets.sincronizar_professores(gestor.professores)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Adicionar professor",
                       f'{nome} <{email}> → módulos: {", ".join(modulos) or "—"}')
    flash(f'Professor "{nome}" adicionado. Já pode registar-se com {email}.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/professor/editar', methods=['POST'])
@apenas_coordenador
def admin_editar_professor():
    """
    Edita um professor (nome, telefone, módulos). O email é a chave (liga o
    login ao papel) e NÃO muda. Sincroniza a tab Professores + auditoria.
    """
    email = request.form.get('email', '').strip()
    nome = request.form.get('nome', '').strip()
    telefone = request.form.get('telefone', '').strip()
    modulos = request.form.getlist('modulos')

    if email == '' or nome == '':
        flash('O professor precisa de nome e email.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    prof = gestor.editar_professor(email, nome=nome, telefone=telefone, modulos=modulos)
    if prof is None:
        flash(f'Não há nenhum professor com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_professores(gestor.professores)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Editar professor",
                       f'{nome} <{email}> → módulos: {", ".join(modulos) or "—"}')
    flash(f'Professor "{nome}" actualizado.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/professor/remover', methods=['POST'])
@apenas_coordenador
def admin_remover_professor():
    """Remove um professor pelo email. Sincroniza a tab Professores + auditoria."""
    email = request.form.get('email', '').strip()
    if email == '':
        flash('Email inválido.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if not gestor.remover_professor(email):
        flash(f'Não há nenhum professor com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_professores(gestor.professores)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Remover professor", f'{email}')
    flash(f'Professor "{email}" removido.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/modulo/remover', methods=['POST'])
@apenas_coordenador
def admin_remover_modulo():
    """
    Remove um módulo (com as suas avaliações e notas) — reservado ao
    coordenador. Limpa a inscrição do módulo nos formandos. Sincroniza as
    tabs Módulos/Notas/Formandos + regista auditoria.
    """
    nome = request.form.get('nome', '').strip()
    if nome == '':
        flash('Módulo inválido.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if not gestor.remover_modulo(nome):
        flash(f'Não há nenhum módulo com o nome "{nome}".', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_modulos(gestor.modulos)
        gsheets.sincronizar_notas(gestor.modulos)
        gsheets.sincronizar_formandos(gestor.formandos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Remover módulo", f'{nome}')
    flash(f'Módulo "{nome}" removido.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/formando', methods=['POST'])
@apenas_coordenador
def admin_adicionar_formando():
    """
    Inscreve um formando (nome + email) e associa-lhe módulos — pela web.

    Gerir inscrições é uma operação de curso (coordenador). O email é a
    chave única; duplicados são barrados. Persistência cirúrgica na tab
    Formandos + auditoria.
    """
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    modulos = request.form.getlist('modulos')

    if nome == '' or email == '':
        flash('O formando precisa de nome e email.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if gestor.formando_existe(email):
        flash(f'Já existe um formando com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    gestor.adicionar_formando(nome, email, modulos)
    if gsheets is not None:
        gsheets.sincronizar_formandos(gestor.formandos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Adicionar formando",
                       f'{nome} <{email}> → módulos: {", ".join(modulos) or "—"}')
    flash(f'Formando "{nome}" inscrito. Já pode registar-se com {email}.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/formando/editar', methods=['POST'])
@apenas_coordenador
def admin_editar_formando():
    """
    Edita um formando (nome e módulos inscritos). O email é a chave (a que
    estão associadas as notas) e NÃO muda aqui — para mudar o email,
    remove-se e volta-se a inscrever. Sincroniza a tab Formandos + auditoria.
    """
    email = request.form.get('email', '').strip()
    nome = request.form.get('nome', '').strip()
    modulos = request.form.getlist('modulos')

    if email == '' or nome == '':
        flash('O formando precisa de nome e email.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    formando = gestor.editar_formando(email, nome=nome, modulos=modulos)
    if formando is None:
        flash(f'Não há nenhum formando com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_formandos(gestor.formandos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Editar formando",
                       f'{nome} <{email}> → módulos: {", ".join(modulos) or "—"}')
    flash(f'Formando "{nome}" atualizado.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/formando/remover', methods=['POST'])
@apenas_coordenador
def admin_remover_formando():
    """
    Remove um formando (direito ao apagamento — RGPD).

    Apaga o formando E as suas notas (o gestor purga as notas em todas as
    avaliações), por isso sincronizamos Formandos + Notas. É deliberadamente
    coordenador-only e regista quem apagou quem (accountability do apagamento).
    """
    email = request.form.get('email', '').strip()
    if email == '':
        flash('Email inválido.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    removeu = gestor.remover_formando(email)
    if not removeu:
        flash(f'Não há nenhum formando com o email "{email}".', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_formandos(gestor.formandos)
        gsheets.sincronizar_notas(gestor.modulos)  # as notas dele foram purgadas
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Remover formando (RGPD)", f'{email} — apagado com as suas notas')
    flash(f'Formando "{email}" removido, incluindo as suas notas (RGPD).', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/modulo/editar', methods=['POST'])
@apenas_staff
def admin_editar_modulo():
    """
    Edita os campos de um módulo já existente (pela web).

    O módulo é identificado pelo 'nome' (campo escondido), que NÃO muda —
    é a chave que liga formandos/avaliações/notas. Editáveis: professor,
    ufcd, horas, estado e as datas (cronograma). Persistência cirúrgica na
    tab Módulos + registo de auditoria.
    """
    nome = request.form.get('nome', '').strip()
    professor = request.form.get('professor', '').strip()
    ufcd = request.form.get('ufcd', '').strip()
    estado = request.form.get('estado', '').strip() or 'planeado'
    horas_totais = _para_int_form(request.form.get('horas_totais', ''))
    # NOTA: as horas DADAS não se editam aqui — são a soma das aulas marcadas
    # como dadas no Cronograma (rota /admin/modulo/datas). As datas/sessões
    # também são geridas à parte, por isso este editar NÃO lhes toca.

    if nome == '':
        flash('Módulo inválido.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, nome):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    actualizado = gestor.editar_modulo(
        nome, professor=professor, horas_totais=horas_totais,
        estado=estado, ufcd=ufcd
    )
    if actualizado is None:
        flash(f'Módulo "{nome}" não encontrado.', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_modulos(gestor.modulos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Editar módulo",
                       f'{nome} → prof. {professor or "—"}, UFCD {ufcd or "—"}, '
                       f'{estado}, total {horas_totais}h')
    flash(f'Módulo "{nome}" actualizado.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/modulo/datas', methods=['POST'])
@apenas_staff
def admin_definir_datas():
    """
    Define/substitui as sessões (aulas) de um módulo.

    Cada sessão traz data + horas + "realizada" (aula dada). As horas dadas do
    módulo passam a ser a SOMA das horas das aulas marcadas como dadas — não há
    campo manual de "horas dadas". Recebe as sessões em JSON (campo escondido
    preenchido pelo editor). Esta rota já NÃO envia avisos: para reagendar uma
    aula e avisar a turma, usa-se a rota dedicada /admin/alteracao.
    Persistência cirúrgica + auditoria; sujeito ao âmbito do professor.
    """
    nome = request.form.get('nome', '').strip()
    try:
        sessoes = json.loads(request.form.get('sessoes', '') or '[]')
    except ValueError:
        sessoes = []
    if not isinstance(sessoes, list):
        sessoes = []

    if nome == '':
        flash('Módulo inválido.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, nome):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    actualizado = gestor.editar_modulo(nome, sessoes=sessoes)
    if actualizado is None:
        flash(f'Módulo "{nome}" não encontrado.', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_modulos(gestor.modulos)
        _invalidar_cache_sheets()

    n_aulas = len(actualizado.datas)
    dadas = sum(1 for s in actualizado.sessoes if s['realizada'])
    registar_auditoria(gsheets, "Definir cronograma",
                       f'{nome}: {n_aulas} aula(s), {actualizado.horas_dadas}/'
                       f'{actualizado.horas_totais}h dadas ({dadas} realizada(s))')
    flash(f'Cronograma de "{nome}" atualizado: {n_aulas} aula(s), '
          f'{actualizado.horas_dadas}h dadas de {actualizado.horas_totais}h.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/avaliacao', methods=['POST'])
@apenas_staff
def admin_adicionar_avaliacao():
    """Adiciona um momento de avaliação a um módulo."""
    modulo = request.form.get('modulo', '').strip()
    data = _data_form_para_ddmm(request.form.get('data', ''))
    tipo = request.form.get('tipo', '').strip()
    descricao = request.form.get('descricao', '').strip()
    objectivo = request.form.get('objectivo', '').strip()
    deliverables = request.form.get('deliverables', '').strip()
    peso_texto = request.form.get('peso', '').strip()
    peso = _para_int_form(peso_texto) if peso_texto != '' else None
    avisar = request.form.get('avisar') == 'on'

    if modulo == '' or descricao == '':
        flash('Indica o módulo e uma descrição para a avaliação.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, modulo):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    criada = gestor.adicionar_avaliacao(modulo, data, tipo, descricao, objectivo, deliverables, peso)
    if criada is None:
        flash(f'Módulo "{modulo}" não encontrado.', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_avaliacoes(gestor.modulos)
        _invalidar_cache_sheets()

    # Avisar a turma, se pedido e se a avaliação tiver data (não faz sentido
    # avisar de uma avaliação ainda sem dia marcado).
    enviados = 0
    if avisar and data != '':
        assunto = 'Nova avaliação marcada — FORAVE'
        mensagem = (f'Foi marcada uma avaliação no módulo "{modulo}": '
                    f'"{descricao}"' + (f' ({tipo})' if tipo else '')
                    + f', no dia {data}.\n\nEntra no site para veres os detalhes.\n')
        enviados = _avisar_turma_do_modulo(gestor, modulo, assunto, mensagem)

    registar_auditoria(gsheets, "Adicionar avaliação",
                       f'{modulo}: {descricao} ({tipo or "—"}, peso {peso if peso is not None else "—"})'
                       + (f' (avisou {enviados})' if avisar else ''))
    if avisar and data == '':
        flash('Avaliação adicionada. (Sem data marcada — não foi enviado aviso.)', 'ok')
    elif avisar:
        flash(f'Avaliação adicionada. {enviados} aviso(s) enviado(s) por email.', 'ok')
    else:
        flash('Avaliação adicionada.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/avaliacao/editar', methods=['POST'])
@apenas_staff
def admin_editar_avaliacao():
    """
    Edita uma avaliação de um módulo (pela posição). As notas já lançadas
    ficam intactas. Âmbito de professor + auditoria; sync cirúrgico.
    """
    modulo = request.form.get('modulo', '').strip()
    indice = _para_int_form(request.form.get('indice', ''), default=-1)
    data = _data_form_para_ddmm(request.form.get('data', ''))
    tipo = request.form.get('tipo', '').strip()
    descricao = request.form.get('descricao', '').strip()
    objectivo = request.form.get('objectivo', '').strip()
    deliverables = request.form.get('deliverables', '').strip()
    peso_texto = request.form.get('peso', '').strip()
    peso = _para_int_form(peso_texto) if peso_texto != '' else None
    avisar = request.form.get('avisar') == 'on'

    if modulo == '' or descricao == '':
        flash('Indica o módulo e uma descrição para a avaliação.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, modulo):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    editada = gestor.editar_avaliacao(modulo, indice, data, tipo, descricao,
                                      objectivo, deliverables, peso)
    if editada is None:
        flash('Módulo ou avaliação inválidos.', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        gsheets.sincronizar_avaliacoes(gestor.modulos)
        _invalidar_cache_sheets()

    enviados = 0
    if avisar and data != '':
        assunto = 'Avaliação atualizada — FORAVE'
        mensagem = (f'A avaliação "{descricao}" do módulo "{modulo}" foi '
                    f'atualizada: fica marcada para o dia {data}.\n\n'
                    f'Entra no site para veres os detalhes.\n')
        enviados = _avisar_turma_do_modulo(gestor, modulo, assunto, mensagem)

    registar_auditoria(gsheets, "Editar avaliação",
                       f'{modulo}, avaliação {indice}: {descricao} '
                       f'({tipo or "—"}, peso {peso if peso is not None else "—"})'
                       + (f' (avisou {enviados})' if avisar else ''))
    if avisar and data == '':
        flash('Avaliação actualizada. (Sem data marcada — não foi enviado aviso.)', 'ok')
    elif avisar:
        flash(f'Avaliação actualizada. {enviados} aviso(s) enviado(s) por email.', 'ok')
    else:
        flash('Avaliação actualizada.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/avaliacao/remover', methods=['POST'])
@apenas_staff
def admin_remover_avaliacao():
    """
    Remove uma avaliação de um módulo (pela posição), com as suas notas.
    Re-sincroniza avaliações + notas (os índices são reescritos). Âmbito de
    professor + auditoria.
    """
    modulo = request.form.get('modulo', '').strip()
    indice = _para_int_form(request.form.get('indice', ''), default=-1)

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tente novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, modulo):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    if not gestor.remover_avaliacao(modulo, indice):
        flash('Módulo ou avaliação inválidos.', 'erro')
        return redirect(url_for('admin'))

    if gsheets is not None:
        # Apagar uma avaliação reindexa as restantes -> re-escrever ambas as tabs
        gsheets.sincronizar_avaliacoes(gestor.modulos)
        gsheets.sincronizar_notas(gestor.modulos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Remover avaliação", f'{modulo}, avaliação {indice}')
    flash('Avaliação removida.', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/nota', methods=['POST'])
@apenas_staff
def admin_lancar_notas():
    """
    Lança/edita as notas de uma avaliação para os alunos inscritos.

    O formulário traz um campo "nota__<email>" por aluno; só os que vierem
    preenchidos (e válidos, 0-20) são lançados.
    """
    modulo = request.form.get('modulo', '').strip()
    indice = _para_int_form(request.form.get('indice', ''), default=-1)

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, modulo):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    alvo = gestor.procurar_modulo(modulo)
    if alvo is None or indice < 0 or indice >= len(alvo.avaliacoes):
        flash('Módulo ou avaliação inválidos.', 'erro')
        return redirect(url_for('admin'))

    avaliacao = alvo.avaliacoes[indice]
    avisar = request.form.get('avisar_notas') == 'on'

    lancadas = 0
    mudancas = []   # para a auditoria: que notas mudaram (aluno=valor)
    a_avisar = []   # {nome, email, nota} para notificar cada aluno (RGPD: só a ele)
    for f in gestor.formandos:
        if not f.esta_inscrito(modulo):
            continue
        valor = request.form.get('nota__' + f.email, '').strip()
        if valor == '':
            continue
        nota = _para_int_form(valor, default=-1)
        if nota < 0 or nota > 20:
            continue  # fora da escala 0-20 — ignora
        anterior = avaliacao.obter_nota(f.email)  # valor antigo (ou None) ANTES de lançar
        if gestor.lancar_nota(modulo, indice, f.email, nota):
            lancadas = lancadas + 1
            # Auditoria com o valor anterior -> novo (accountability completa:
            # "de quanto para quanto mudou a nota, e por quem").
            antes = anterior if anterior is not None else '—'
            mudancas.append(f'{f.email}: {antes}→{nota}')
            a_avisar.append({'nome': f.nome, 'email': f.email, 'nota': nota})

    if gsheets is not None:
        gsheets.sincronizar_notas(gestor.modulos)
        _invalidar_cache_sheets()

    # Notificar cada aluno da SUA nota — email INDIVIDUAL. RGPD: a nota de um
    # aluno vai só para esse aluno (nunca em conjunto). Opcional e robusto
    # (nunca parte a página se o email falhar).
    avisados = 0
    if avisar and a_avisar:
        try:
            sender = carregar_email()
            if sender.configurado:
                assunto = 'Nota lançada — FORAVE'
                reply_to = _reply_to_actual()
                for a in a_avisar:
                    corpo = (f"Olá {a['nome']},\n\n"
                             f"Foi lançada a tua nota da avaliação "
                             f"\"{avaliacao.descricao}\" do módulo \"{modulo}\": "
                             f"{a['nota']} (escala 0-20).\n\n"
                             f"Entra no site para veres o teu percurso completo.\n")
                    if sender.enviar(a['email'], a['nome'], assunto, corpo,
                                     reply_to=reply_to):
                        avisados = avisados + 1
        except Exception as erro:
            print(f"[NOTAS] Erro ao avisar os alunos: {erro}")

    if lancadas > 0:
        # Detalhe granular: exactamente que notas foram lançadas/alteradas,
        # para que a auditoria responda a "quem pôs esta nota a este aluno?".
        registar_auditoria(gsheets, "Lançar notas",
                           f'{modulo}, avaliação {indice}: ' + ', '.join(mudancas)
                           + (f' (avisou {avisados})' if avisar else ''))
    if avisar and lancadas > 0:
        flash(f'{lancadas} nota(s) lançada(s). {avisados} aluno(s) avisado(s) por email.', 'ok')
    else:
        flash(f'{lancadas} nota(s) lançada(s).', 'ok')
    return redirect(url_for('admin'))


@app.route('/admin/alteracao', methods=['POST'])
@apenas_staff
def admin_registar_alteracao():
    """
    Regista uma alteração ao cronograma (mudar uma data) e,
    opcionalmente, avisa a turma por email.

    É o coração original do projecto (notificar mudanças) trazido para a
    web. A escrita é cirúrgica: sincroniza só as tabs Alterações e
    Cronograma (a data do módulo muda). O aviso por email é opcional
    (caixa "avisar") e robusto (nunca parte a página se o email falhar).
    """
    modulo = request.form.get('modulo', '').strip()
    data_original = _data_form_para_ddmm(request.form.get('data_original', ''))
    data_nova = _data_form_para_ddmm(request.form.get('data_nova', ''))
    motivo = request.form.get('motivo', '').strip()
    avisar = request.form.get('avisar') == 'on'
    autor = utilizador_actual() or 'coordenador'

    if modulo == '' or data_original == '' or data_nova == '':
        flash('Indica o módulo, a data original e a nova data.', 'erro')
        return redirect(url_for('admin'))

    gestor, gsheets = gestor_para_escrita()
    if gestor is None:
        flash('Sem ligação ao Google Sheet — tenta novamente.', 'erro')
        return redirect(url_for('admin'))

    if gestor.procurar_modulo(modulo) is None:
        flash(f'Módulo "{modulo}" não encontrado.', 'erro')
        return redirect(url_for('admin'))

    if not pode_gerir_modulo(gestor, modulo):
        flash('Só pode gerir os seus módulos.', 'erro')
        return redirect(url_for('admin'))

    notificacao = gestor.registar_alteracao(modulo, data_original, data_nova, motivo, autor)

    # Persistir cirurgicamente: alterações (nova) + módulos (datas mudaram)
    if gsheets is not None:
        gsheets.sincronizar_alteracoes(gestor.alteracoes)
        gsheets.sincronizar_modulos(gestor.modulos)
        _invalidar_cache_sheets()

    registar_auditoria(gsheets, "Alterar cronograma",
                       f'{modulo}: {data_original} → {data_nova}'
                       + (f' (motivo: {motivo})' if motivo else ''))

    # Avisar a turma por email, se pedido (e se o email estiver configurado).
    enviados = 0
    if avisar and notificacao is not None:
        try:
            sender = carregar_email()
            if sender.configurado:
                reply_to = _reply_to_actual()
                for d in notificacao.destinatarios:
                    if sender.enviar(d['email'], d['nome'],
                                     'Alteração ao cronograma — FORAVE',
                                     notificacao.mensagem, reply_to=reply_to):
                        enviados = enviados + 1
        except Exception as erro:
            print(f"[ALTERACAO] Erro ao enviar avisos por email: {erro}")

    if notificacao is None:
        flash('Alteração registada (sem destinatários para avisar).', 'ok')
    elif avisar:
        flash(f'Alteração registada. {enviados} aviso(s) enviado(s) por email.', 'ok')
    else:
        flash('Alteração registada.', 'ok')
    return redirect(url_for('admin'))


def _para_int_form(valor, default=0):
    """Converte um campo de formulário em inteiro, com segurança."""
    valor = str(valor).strip()
    if valor == '':
        return default
    try:
        return int(float(valor))
    except ValueError:
        return default


def _texto_para_lista_form(texto):
    """Converte 'a, b, c' (campo de formulário) numa lista ['a','b','c']."""
    lista = []
    for parte in str(texto).split(','):
        parte = parte.strip()
        if parte != '':
            lista.append(parte)
    return lista


def _data_form_para_ddmm(texto):
    """Normaliza uma data vinda de um formulário para o formato dd/mm/aaaa.

    Os campos de calendário (`<input type="date">`) enviam a data em ISO
    (aaaa-mm-dd), mas o sistema guarda e mostra as datas em dd/mm/aaaa. Esta
    função converte o formato ISO; qualquer outro valor (já em dd/mm/aaaa, ou
    vazio) é devolvido tal como está. Assim o calendário pode ser usado sem
    partir a consistência das datas no resto do programa.
    """
    texto = str(texto).strip()
    partes = texto.split('-')
    if (len(partes) == 3 and len(partes[0]) == 4
            and all(p.isdigit() for p in partes)):
        return f'{partes[2]}/{partes[1]}/{partes[0]}'
    return texto


def _reply_to_actual():
    """Email de quem está a despoletar o aviso, para o "Responder" do
    destinatário ir ter com essa pessoa (ex.: o professor).

    O REMETENTE do email não muda — é sempre o institucional (verificado na
    Brevo). Só se define o cabeçalho Reply-To. Devolve None se não houver um
    email válido na sessão (nesse caso o email sai sem Reply-To).
    """
    email = utilizador_actual()
    if email and "@" in email:
        return email
    return None


def _avisar_turma_do_modulo(gestor, modulo, assunto, mensagem):
    """Envia (individualmente) o mesmo aviso a cada aluno inscrito no módulo.

    Envio um-a-um (um email por aluno) — nunca expõe os endereços dos outros
    (RGPD). Robusto: apanha qualquer erro para nunca partir a página de quem
    chama. Devolve o número de avisos que o serviço de email aceitou.

    O "Responder" do email vai para quem despoletou o aviso (professor ou
    coordenador), via Reply-To — o remetente continua institucional.

    É o mesmo padrão usado ao reagendar uma aula, agora reutilizado para as
    avaliações.
    """
    enviados = 0
    try:
        sender = carregar_email()
        if not sender.configurado:
            return 0
        reply_to = _reply_to_actual()
        for f in gestor.formandos:
            if f.esta_inscrito(modulo):
                if sender.enviar(f.email, f.nome, assunto, mensagem,
                                 reply_to=reply_to):
                    enviados = enviados + 1
    except Exception as erro:
        print(f"[AVISO] Erro ao avisar a turma de {modulo}: {erro}")
    return enviados


@app.template_filter('data_iso')
def _data_iso(texto):
    """Filtro Jinja: converte dd/mm/aaaa -> aaaa-mm-dd.

    Serve para preencher o valor de um `<input type="date">` a partir de uma
    data guardada em dd/mm/aaaa. Se a data não estiver nesse formato, devolve ''
    (o calendário fica vazio, em vez de mostrar algo inválido).
    """
    partes = str(texto).strip().split('/')
    if len(partes) == 3 and all(p.isdigit() for p in partes):
        return f'{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}'
    return ''


@app.route('/api/schedule', methods=['GET'])
@login_obrigatorio
def get_schedule_data():
    """
    Devolve os módulos reais em JSON para o frontend desenhar.

    Cada módulo leva o progresso de horas já calculado pelos
    métodos do domínio (horas_restantes, percentagem_concluida).
    """
    try:
        gestor = carregar_gestor()

        # Padrão lista vazia + for + append (Aula 6) — sem list comp.
        modulos = []
        for m in gestor.modulos:
            dados = {}
            dados["ufcd"] = m.ufcd
            dados["nome"] = m.nome
            dados["professor"] = m.professor
            dados["horas_totais"] = m.horas_totais
            dados["horas_dadas"] = m.horas_dadas
            dados["horas_restantes"] = m.horas_restantes()
            dados["percentagem"] = round(m.percentagem_concluida(), 1)
            dados["estado"] = m.estado
            dados["datas"] = m.datas
            dados["num_avaliacoes"] = len(m.avaliacoes)
            modulos.append(dados)

        return jsonify(modulos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/insights', methods=['GET'])
@login_obrigatorio
def get_insights():
    """Devolve os indicadores calculados a partir dos dados reais."""
    try:
        gestor = carregar_gestor()
        motor = InsightsEngine(gestor)
        return jsonify(motor.analisar())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/export_pdf', methods=['POST'])
@login_obrigatorio
def export_pdf():
    """
    Exporta um relatório PDF com os módulos e as suas avaliações.

    Evolução (Bloco 3): antes gerava um horário fictício em 3 vistas
    (diária/semanal/mensal). Agora gera um relatório real do estado
    do curso — uma tabela de módulos (com progresso) e uma tabela
    de avaliações — que é o que o sistema efectivamente gere.
    """
    try:
        gestor = carregar_gestor()
        pdf = gerar_relatorio_pdf(gestor)
        return send_file(
            pdf, mimetype='application/pdf', as_attachment=True,
            download_name='relatorio_cronograma.pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def gerar_relatorio_pdf(gestor):
    """
    Constrói o PDF do relatório (módulos + avaliações) em memória.

    Parâmetros:
        gestor (GestorCronograma): fonte dos dados.

    Retorna:
        BytesIO: buffer com o PDF, pronto para send_file().
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=0.5 * cm, leftMargin=0.5 * cm,
        topMargin=0.5 * cm, bottomMargin=0.5 * cm
    )
    elementos = []

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'TituloRelatorio', parent=estilos['Heading1'],
        fontSize=16, textColor=colors.HexColor('#667eea'),
        spaceAfter=12, alignment=1
    )

    # --- Tabela de módulos ---
    elementos.append(Paragraph("<b>Relatório de Módulos — FORAVE</b>", estilo_titulo))
    elementos.append(Spacer(1, 0.3 * cm))

    tabela_modulos = [["UFCD", "Módulo", "Professor", "Horas (dadas/totais)",
                       "Progresso", "Estado"]]
    for m in gestor.modulos:
        linha = [
            m.ufcd,
            m.nome,
            m.professor,
            f"{m.horas_dadas}/{m.horas_totais}",
            f"{round(m.percentagem_concluida(), 1)}%",
            m.estado
        ]
        tabela_modulos.append(linha)

    t = Table(tabela_modulos, colWidths=[2 * cm, 6 * cm, 5 * cm, 4 * cm, 3 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
    ]))
    elementos.append(t)

    # --- Tabela de avaliações (uma linha por momento) ---
    elementos.append(Spacer(1, 0.6 * cm))
    elementos.append(Paragraph("<b>Avaliações</b>", estilo_titulo))
    elementos.append(Spacer(1, 0.3 * cm))

    tabela_av = [["Módulo", "Data", "Tipo", "Descrição", "Peso"]]
    for m in gestor.modulos:
        for av in m.avaliacoes:
            if av.peso is None:
                peso_texto = "-"
            else:
                peso_texto = f"{av.peso}%"
            tabela_av.append([m.nome, av.data, av.tipo, av.descricao, peso_texto])

    # Se não houver avaliações, mostrar uma linha informativa
    if len(tabela_av) == 1:
        tabela_av.append(["—", "—", "—", "Sem avaliações registadas", "—"])

    t2 = Table(tabela_av, colWidths=[6 * cm, 3 * cm, 3 * cm, 9 * cm, 2 * cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
    ]))
    elementos.append(t2)

    doc.build(elementos)
    buffer.seek(0)
    return buffer


# ============================================================
# Cabeçalhos de segurança + páginas de erro (boas práticas)
# ============================================================

@app.after_request
def _cabecalhos_seguranca(resposta):
    """
    Adiciona cabeçalhos de segurança a todas as respostas.

    São práticas-padrão da indústria, "de graça" e sem efeitos visíveis:
      - X-Content-Type-Options: nosniff -> o browser não "adivinha" o tipo
        do conteúdo (evita alguns ataques de MIME sniffing).
      - X-Frame-Options: SAMEORIGIN -> impede que o site seja embutido num
        <iframe> de outro domínio (proteção contra clickjacking).
      - Referrer-Policy -> não vaza o URL completo para sites externos.
      - Permissions-Policy -> desliga APIs sensíveis que não usamos.
    Não usamos Content-Security-Policy restritiva para não partir os CDNs
    (Bootstrap/Chart.js) nem os pequenos scripts inline das páginas.
    """
    resposta.headers['X-Content-Type-Options'] = 'nosniff'
    resposta.headers['X-Frame-Options'] = 'SAMEORIGIN'
    resposta.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    resposta.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return resposta


@app.errorhandler(403)
def erro_403(e):
    """Acesso negado (ex.: token de módulo inválido/expirado) — página com a marca."""
    return render_template('erro.html', codigo=403, titulo='Acesso negado',
                           mensagem='Não tens permissão para ver isto, ou o link '
                                    'já expirou. Volta ao início e entra pela porta certa.'), 403


@app.errorhandler(404)
def erro_404(e):
    """Página não encontrada — página com a marca (em vez da feia por omissão)."""
    return render_template('erro.html', codigo=404, titulo='Página não encontrada',
                           mensagem='O endereço que procuras não existe ou foi movido.'), 404


@app.errorhandler(500)
def erro_500(e):
    """Erro interno — página com a marca, sem expor detalhes técnicos ao utilizador."""
    return render_template('erro.html', codigo=500, titulo='Ocorreu um erro',
                           mensagem='Algo correu mal do nosso lado. Tenta novamente '
                                    'daqui a pouco.'), 500


if __name__ == '__main__':
    app.run(debug=True)
