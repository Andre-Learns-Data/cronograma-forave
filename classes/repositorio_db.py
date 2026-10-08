# ============================================================
# repositorio_db.py — Persistência em base de dados (SQLAlchemy)
# ============================================================
# Evolução (Out/2026): a persistência passa de ficheiros JSON /
# Google Sheets para uma BASE DE DADOS RELACIONAL de verdade.
#
#   - Em desenvolvimento/demo:  SQLite  (um ficheiro, zero instalação)
#   - Em produção (cloud):      PostgreSQL (base de dados gerida)
#
# A base de dados a usar é escolhida pela variável de ambiente
# DATABASE_URL — o MESMO código serve para as duas. É o SQLAlchemy
# que trata de falar o "dialeto" de SQL certo para cada uma.
#
# IDEIA-CHAVE (padrão repositório / inversão de dependência):
# esta camada fala exatamente o mesmo "dialeto de dicionários" que
# o JSON falava. Recebe e devolve os MESMOS dicionários que o
# to_dict()/from_dict() das classes produzem. Assim, o domínio
# (classes/ e gestor_cronograma.py) fica intacto — nunca sabe se
# está a gravar num ficheiro ou numa base de dados.
#
# Porquê base de dados e não a folha de cálculo:
#   - transações (grava tudo ou não grava nada — o JSON não garantia)
#   - integridade referencial (uma nota não existe sem a sua avaliação)
#   - acaba o "override" da sincronização num só sentido da Sheets
# ============================================================

import os

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)

# ------------------------------------------------------------
# ESQUEMA — as tabelas e as suas relações
# ------------------------------------------------------------
# O que no JSON estava aninhado (um módulo tinha lá dentro as suas
# sessões, avaliações e notas) passa aqui a tabelas próprias ligadas
# por chaves estrangeiras (ForeignKey). É a forma relacional correta.
# A coluna "ordem" preserva a ordem original das listas.

metadata = MetaData()

modulos = Table(
    "modulos", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("ufcd", String),
    Column("nome", String),
    Column("professor", String),
    Column("horas_totais", Integer),
    Column("horas_dadas", Integer),
    Column("estado", String),
)

# As datas do cronograma de um módulo (lista de strings).
modulo_datas = Table(
    "modulo_datas", metadata,
    Column("id", Integer, primary_key=True),
    Column("modulo_id", Integer, ForeignKey("modulos.id")),
    Column("ordem", Integer),
    Column("data", String),
)

# As sessões "ricas" de um módulo (data + horas + se foi dada).
sessoes = Table(
    "sessoes", metadata,
    Column("id", Integer, primary_key=True),
    Column("modulo_id", Integer, ForeignKey("modulos.id")),
    Column("ordem", Integer),
    Column("data", String),
    Column("horas", Integer),
    Column("realizada", Boolean),
)

# As avaliações de um módulo.
avaliacoes = Table(
    "avaliacoes", metadata,
    Column("id", Integer, primary_key=True),
    Column("modulo_id", Integer, ForeignKey("modulos.id")),
    Column("ordem", Integer),
    Column("data", String),
    Column("tipo", String),
    Column("descricao", String),
    Column("objectivo", String),
    Column("deliverables", String),
    Column("peso", Integer, nullable=True),
)

# As notas de uma avaliação (uma linha por aluno — era um dict email:valor).
notas = Table(
    "notas", metadata,
    Column("id", Integer, primary_key=True),
    Column("avaliacao_id", Integer, ForeignKey("avaliacoes.id")),
    Column("email", String),
    Column("valor", Float),
)

professores = Table(
    "professores", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("nome", String),
    Column("email", String),
    Column("telefone", String),
)

# Relação muitos-para-muitos: um professor gere vários módulos (por nome).
professor_modulos = Table(
    "professor_modulos", metadata,
    Column("id", Integer, primary_key=True),
    Column("professor_id", Integer, ForeignKey("professores.id")),
    Column("ordem", Integer),
    Column("modulo_nome", String),
)

formandos = Table(
    "formandos", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("nome", String),
    Column("email", String),
)

# Relação muitos-para-muitos: um formando está inscrito em vários módulos.
formando_modulos = Table(
    "formando_modulos", metadata,
    Column("id", Integer, primary_key=True),
    Column("formando_id", Integer, ForeignKey("formandos.id")),
    Column("ordem", Integer),
    Column("modulo_nome", String),
)

alteracoes = Table(
    "alteracoes", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("modulo_nome", String),
    Column("data_original", String),
    Column("data_nova", String),
    Column("motivo", String),
    Column("autor", String),
    Column("data_registo", String),
)

notificacoes = Table(
    "notificacoes", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("mensagem", Text),
    Column("data_criacao", String),
    Column("enviada", Boolean),
)

notif_destinatarios = Table(
    "notif_destinatarios", metadata,
    Column("id", Integer, primary_key=True),
    Column("notif_id", Integer, ForeignKey("notificacoes.id")),
    Column("ordem", Integer),
    Column("email", String),
    Column("nome", String),
)

utilizadores = Table(
    "utilizadores", metadata,
    Column("id", Integer, primary_key=True),
    Column("ordem", Integer),
    Column("email", String),
    Column("papel", String),
    Column("password_hash", Text),
)

# Registo de auditoria (append-only): quem fez o quê e quando.
# Ao contrário das outras tabelas, nunca é apagada e reescrita — cada
# acção é só um INSERT novo (é mais eficiente e mais seguro que reescrever
# o ficheiro inteiro, como o JSON fazia a cada registo).
auditoria = Table(
    "auditoria", metadata,
    Column("id", Integer, primary_key=True),
    Column("data_hora", String),
    Column("autor", String),
    Column("accao", String),
    Column("detalhe", Text),
)


# ------------------------------------------------------------
# LIGAÇÃO À BASE DE DADOS
# ------------------------------------------------------------

def criar_engine(database_url=None):
    """
    Cria o "engine" do SQLAlchemy — o objecto que sabe ligar-se à
    base de dados. É a DATABASE_URL que decide qual:

      - vazia / ausente  -> SQLite local (ficheiro dados/cronograma.db)
      - postgresql://... -> PostgreSQL (produção)

    Assim o mesmo código corre em dev e em produção; só muda a variável.
    """
    if database_url is None:
        database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        # Por defeito: SQLite dentro da pasta dados/ (criada se faltar).
        os.makedirs("dados", exist_ok=True)
        database_url = "sqlite:///dados/cronograma.db"

    # O Render entrega URLs a começar por 'postgres://', mas o SQLAlchemy
    # moderno quer 'postgresql://'. Corrige-se aqui para não rebentar.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return create_engine(database_url)


def criar_tabelas(engine):
    """Cria as tabelas se ainda não existirem (não apaga dados)."""
    metadata.create_all(engine)


def _num(valor):
    """
    Devolve uma nota como int quando é um número inteiro (14 em vez de
    14.0) e como float quando tem casas decimais (14.5). Mantém o
    formato igual ao que estava no JSON.
    """
    if valor is None:
        return None
    f = float(valor)
    return int(f) if f.is_integer() else f


# ------------------------------------------------------------
# GRAVAR — recebe os mesmos dicts que iam para o JSON
# ------------------------------------------------------------
# A gravação está separada em dois âmbitos porque o gestor (as 5
# entidades do cronograma) e a autenticação (os utilizadores) gravam
# em MOMENTOS diferentes. Se fosse tudo junto, gravar um apagava o
# outro. Cada âmbito tem a sua transação, sobre as suas tabelas.

# Tabelas do âmbito do GESTOR (filhos antes dos pais, por causa das FKs).
_TABELAS_GESTOR = (notas, avaliacoes, sessoes, modulo_datas, modulos,
                   professor_modulos, professores,
                   formando_modulos, formandos,
                   notif_destinatarios, notificacoes, alteracoes)


def _apagar(conn, tabelas):
    for tabela in tabelas:
        conn.execute(delete(tabela))


def _inserir_modulos(conn, modulos_dados):
    for i, m in enumerate(modulos_dados):
        res = conn.execute(insert(modulos).values(
            ordem=i, ufcd=m.get("ufcd", ""), nome=m["nome"],
            professor=m["professor"], horas_totais=m["horas_totais"],
            horas_dadas=m["horas_dadas"], estado=m["estado"],
        ))
        modulo_id = res.inserted_primary_key[0]

        for j, data in enumerate(m.get("datas", [])):
            conn.execute(insert(modulo_datas).values(
                modulo_id=modulo_id, ordem=j, data=data))

        for j, s in enumerate(m.get("sessoes", [])):
            conn.execute(insert(sessoes).values(
                modulo_id=modulo_id, ordem=j, data=s["data"],
                horas=s["horas"], realizada=s["realizada"]))

        for j, av in enumerate(m.get("avaliacoes", [])):
            res_av = conn.execute(insert(avaliacoes).values(
                modulo_id=modulo_id, ordem=j, data=av["data"],
                tipo=av["tipo"], descricao=av["descricao"],
                objectivo=av["objectivo"], deliverables=av["deliverables"],
                peso=av.get("peso")))
            av_id = res_av.inserted_primary_key[0]
            for email, valor in av.get("notas", {}).items():
                conn.execute(insert(notas).values(
                    avaliacao_id=av_id, email=email, valor=valor))


def _inserir_professores(conn, professores_dados):
    for i, p in enumerate(professores_dados):
        res = conn.execute(insert(professores).values(
            ordem=i, nome=p["nome"], email=p["email"],
            telefone=p.get("telefone", "")))
        pid = res.inserted_primary_key[0]
        for j, nome_mod in enumerate(p.get("modulos", [])):
            conn.execute(insert(professor_modulos).values(
                professor_id=pid, ordem=j, modulo_nome=nome_mod))


def _inserir_formandos(conn, formandos_dados):
    for i, f in enumerate(formandos_dados):
        res = conn.execute(insert(formandos).values(
            ordem=i, nome=f["nome"], email=f["email"]))
        fid = res.inserted_primary_key[0]
        for j, nome_mod in enumerate(f.get("modulos", [])):
            conn.execute(insert(formando_modulos).values(
                formando_id=fid, ordem=j, modulo_nome=nome_mod))


def _inserir_alteracoes(conn, alteracoes_dados):
    for i, a in enumerate(alteracoes_dados):
        conn.execute(insert(alteracoes).values(
            ordem=i, modulo_nome=a["modulo_nome"],
            data_original=a["data_original"], data_nova=a["data_nova"],
            motivo=a["motivo"], autor=a["autor"],
            data_registo=a["data_registo"]))


def _inserir_notificacoes(conn, notificacoes_dados):
    for i, n in enumerate(notificacoes_dados):
        res = conn.execute(insert(notificacoes).values(
            ordem=i, mensagem=n["mensagem"],
            data_criacao=n["data_criacao"], enviada=n["enviada"]))
        nid = res.inserted_primary_key[0]
        for j, dest in enumerate(n.get("destinatarios", [])):
            conn.execute(insert(notif_destinatarios).values(
                notif_id=nid, ordem=j, email=dest["email"],
                nome=dest["nome"]))


def _inserir_utilizadores(conn, utilizadores_dados):
    for i, u in enumerate(utilizadores_dados):
        conn.execute(insert(utilizadores).values(
            ordem=i, email=u["email"], papel=u["papel"],
            password_hash=u["password_hash"]))


def guardar_gestor(engine, modulos_dados, professores_dados, formandos_dados,
                   alteracoes_dados, notificacoes_dados):
    """
    Grava as 5 entidades do cronograma numa só transação (ou tudo, ou
    nada). Apaga e reescreve — estratégia simples e segura para este
    volume (~10 módulos). Não toca na tabela de utilizadores.
    """
    criar_tabelas(engine)
    with engine.begin() as conn:
        _apagar(conn, _TABELAS_GESTOR)
        _inserir_modulos(conn, modulos_dados)
        _inserir_professores(conn, professores_dados)
        _inserir_formandos(conn, formandos_dados)
        _inserir_alteracoes(conn, alteracoes_dados)
        _inserir_notificacoes(conn, notificacoes_dados)


def guardar_utilizadores(engine, utilizadores_dados):
    """Grava as contas de login numa transação própria."""
    criar_tabelas(engine)
    with engine.begin() as conn:
        _apagar(conn, (utilizadores,))
        _inserir_utilizadores(conn, utilizadores_dados)


def guardar_tudo(engine, modulos_dados, professores_dados, formandos_dados,
                 alteracoes_dados, notificacoes_dados, utilizadores_dados):
    """Atalho: grava os dois âmbitos (usado pelo seed e pelos testes)."""
    guardar_gestor(engine, modulos_dados, professores_dados, formandos_dados,
                   alteracoes_dados, notificacoes_dados)
    guardar_utilizadores(engine, utilizadores_dados)


# ------------------------------------------------------------
# CARREGAR — devolve os mesmos dicts que o JSON devolvia
# ------------------------------------------------------------

def carregar_gestor(engine):
    """
    Lê as 5 entidades do cronograma e reconstrói os dicionários
    exatamente na forma que o from_dict() das classes espera —
    idêntica à que o json.load() devolvia.

    Devolve um dict com as cinco listas:
      modulos, professores, formandos, alteracoes, notificacoes
    """
    criar_tabelas(engine)
    with engine.connect() as conn:
        # --- Módulos ---
        lista_modulos = []
        for m in conn.execute(select(modulos).order_by(modulos.c.ordem, modulos.c.id)):
            datas = []
            for r in conn.execute(
                    select(modulo_datas)
                    .where(modulo_datas.c.modulo_id == m.id)
                    .order_by(modulo_datas.c.ordem)):
                datas.append(r.data)

            lista_sessoes = []
            for r in conn.execute(
                    select(sessoes)
                    .where(sessoes.c.modulo_id == m.id)
                    .order_by(sessoes.c.ordem)):
                lista_sessoes.append({
                    "data": r.data, "horas": r.horas,
                    "realizada": bool(r.realizada),
                })

            lista_avaliacoes = []
            for av in conn.execute(
                    select(avaliacoes)
                    .where(avaliacoes.c.modulo_id == m.id)
                    .order_by(avaliacoes.c.ordem)):
                notas_dict = {}
                for nrow in conn.execute(
                        select(notas).where(notas.c.avaliacao_id == av.id)):
                    notas_dict[nrow.email] = _num(nrow.valor)
                lista_avaliacoes.append({
                    "data": av.data, "tipo": av.tipo, "descricao": av.descricao,
                    "objectivo": av.objectivo, "deliverables": av.deliverables,
                    "peso": av.peso, "notas": notas_dict,
                })

            lista_modulos.append({
                "ufcd": m.ufcd, "nome": m.nome, "professor": m.professor,
                "horas_totais": m.horas_totais, "horas_dadas": m.horas_dadas,
                "estado": m.estado, "datas": datas,
                "sessoes": lista_sessoes, "avaliacoes": lista_avaliacoes,
            })

        # --- Professores ---
        lista_professores = []
        for p in conn.execute(select(professores).order_by(professores.c.ordem, professores.c.id)):
            mods = []
            for r in conn.execute(
                    select(professor_modulos)
                    .where(professor_modulos.c.professor_id == p.id)
                    .order_by(professor_modulos.c.ordem)):
                mods.append(r.modulo_nome)
            lista_professores.append({
                "nome": p.nome, "email": p.email,
                "telefone": p.telefone, "modulos": mods,
            })

        # --- Formandos ---
        lista_formandos = []
        for f in conn.execute(select(formandos).order_by(formandos.c.ordem, formandos.c.id)):
            mods = []
            for r in conn.execute(
                    select(formando_modulos)
                    .where(formando_modulos.c.formando_id == f.id)
                    .order_by(formando_modulos.c.ordem)):
                mods.append(r.modulo_nome)
            lista_formandos.append({
                "nome": f.nome, "email": f.email, "modulos": mods,
            })

        # --- Alterações ---
        lista_alteracoes = []
        for a in conn.execute(select(alteracoes).order_by(alteracoes.c.ordem, alteracoes.c.id)):
            lista_alteracoes.append({
                "modulo_nome": a.modulo_nome, "data_original": a.data_original,
                "data_nova": a.data_nova, "motivo": a.motivo, "autor": a.autor,
                "data_registo": a.data_registo,
            })

        # --- Notificações ---
        lista_notificacoes = []
        for n in conn.execute(select(notificacoes).order_by(notificacoes.c.ordem, notificacoes.c.id)):
            dests = []
            for r in conn.execute(
                    select(notif_destinatarios)
                    .where(notif_destinatarios.c.notif_id == n.id)
                    .order_by(notif_destinatarios.c.ordem)):
                dests.append({"email": r.email, "nome": r.nome})
            lista_notificacoes.append({
                "mensagem": n.mensagem, "destinatarios": dests,
                "data_criacao": n.data_criacao, "enviada": bool(n.enviada),
            })

    return {
        "modulos": lista_modulos,
        "professores": lista_professores,
        "formandos": lista_formandos,
        "alteracoes": lista_alteracoes,
        "notificacoes": lista_notificacoes,
    }


def carregar_utilizadores(engine):
    """Lê as contas de login (lista de dicts email/papel/password_hash)."""
    criar_tabelas(engine)
    with engine.connect() as conn:
        lista = []
        for u in conn.execute(
                select(utilizadores).order_by(utilizadores.c.ordem, utilizadores.c.id)):
            lista.append({
                "email": u.email, "papel": u.papel,
                "password_hash": u.password_hash,
            })
        return lista


def carregar_tudo(engine):
    """Atalho: junta o gestor + utilizadores (usado pelos testes)."""
    dados = carregar_gestor(engine)
    dados["utilizadores"] = carregar_utilizadores(engine)
    return dados


# ------------------------------------------------------------
# AUDITORIA (append-only — só insere, nunca reescreve)
# ------------------------------------------------------------

def registar_auditoria(engine, data_hora, autor, accao, detalhe):
    """Acrescenta UMA entrada de auditoria. É só um INSERT (append-only)."""
    criar_tabelas(engine)
    with engine.begin() as conn:
        conn.execute(insert(auditoria).values(
            data_hora=data_hora, autor=autor, accao=accao, detalhe=detalhe))


def ler_auditoria(engine):
    """
    Lê todas as entradas de auditoria por ordem de inserção (as mais
    antigas primeiro). Quem chama é que inverte/corta, como já fazia
    com o JSON.
    """
    criar_tabelas(engine)
    with engine.connect() as conn:
        lista = []
        for r in conn.execute(select(auditoria).order_by(auditoria.c.id)):
            lista.append({
                "data_hora": r.data_hora, "autor": r.autor,
                "accao": r.accao, "detalhe": r.detalhe,
            })
        return lista
