# ============================================================
# seed_demo.py — Semeia DADOS DE DEMONSTRAÇÃO
# ============================================================
# Enche o sistema com o curso REAL (EGICD — Técnico/a Especialista em
# Gestão de Informação e Ciência dos Dados) e cria as contas de acesso —
# tudo num só comando, para a demo estar pronta em segundos.
#
# Como os 3 canais LOCAIS (terminal `main.py`, web `app.py` e o `.exe`)
# leem os MESMOS ficheiros `dados/*.json`, este script serve os três.
#
# Correr:   python seed_demo.py            (escreve na pasta "dados/")
#           python seed_demo.py <pasta>    (escreve noutra pasta — testes)
#
# É seguro correr mais do que uma vez: carrega o que já existe e só
# ACRESCENTA o que falta (não apaga nada). Numa cópia limpa (pasta
# "dados/" vazia) fica com a demo toda.
#
# CONTAS (todas com a mesma password de demo — ver PASSWORD_DEMO):
#   - Coordenador: chronosforave@gmail.com    (vê/gere tudo)
#   - Professor:   luis.cerejeira@forave.pt    (vê só os módulos dele)
#   - Aluno:       alunoforavecetdados@gmail.com (vê as suas notas + recebe
#                  os avisos automáticos — é a MESMA conta da demo de email)
#
# REGRAS DA DEMO (decididas com o André):
#   - Só o módulo do Prof. Cerejeira (Programação Avançada com Python) tem
#     CRONOGRAMA; os restantes ficam listados em "pendente", sem datas —
#     não se inventa calendário de aulas que ainda não foram dadas.
#   - A última aula do Cerejeira fica em 30/09/2026 (o previsto) — é a que
#     se REAGENDA ao vivo para 14/10/2026 na demo.
#   - O Inglês Técnico (UFCD 5745, Prof. Ricardo Mendes) NÃO é semeado:
#     importa-se ao vivo a partir de importar_modulos_demo.csv.
# ============================================================

import os
import sys

from classes.autenticacao import GestorAutenticacao
from gestor_cronograma import GestorCronograma

# ------------------------------------------------------------
# Contas e password de demo
# ------------------------------------------------------------
PASSWORD_DEMO = "demo1234"
COORDENADOR = "chronosforave@gmail.com"
PROFESSOR_PRINCIPAL = "luis.cerejeira@forave.pt"
# Aluno de demonstração com email REAL: serve de persona "aluno" E de
# destinatário dos avisos automáticos (nota individual / reagendamento).
EMAIL_ALUNO_TESTE = "alunoforavecetdados@gmail.com"

# ------------------------------------------------------------
# Nomes dos módulos (constantes para o vínculo professor<->módulo bater certo)
# ------------------------------------------------------------
M_PY_AV = "Programação Avançada com Python"

# Professores do curso (nome, email, telefone, [módulos]). O vínculo ao
# módulo é por nome (campo 'professor' de cada módulo), por isso a lista
# de módulos aqui pode ficar vazia.
PROFESSORES = [
    ("Luís Cerejeira", PROFESSOR_PRINCIPAL, "", []),
    ("Ana Teixeira", "ana.teixeira@forave.pt", "", []),
    ("Alberto Pereira", "alberto.pereira@forave.pt", "", []),
    ("Carlos Vicente", "carlos.vicente@forave.pt", "", []),
    ("José Ramalhoto", "jose.ramalhoto@forave.pt", "", []),
    ("Nuno Barbosa", "nuno.barbosa@forave.pt", "", []),
    ("Paulo Cunha", "paulo.cunha@forave.pt", "", []),
    ("Rui Chilro", "rui.chilro@forave.pt", "", []),
    ("Stéphanie Dermagne", "stephanie.dermagne@forave.pt", "", []),
    ("Ricardo Mendes", "ricardo.mendes@forave.pt", "", []),
]


def _sessoes(datas, horas_cada, n_dadas):
    """
    Constrói a lista de sessões de um módulo para o seed.

    Cada aula fica com `horas_cada` horas; as primeiras `n_dadas` ficam
    marcadas como "dadas" (é essa marca que soma às horas dadas do módulo).
    """
    return [{"data": d, "horas": horas_cada, "realizada": i < n_dadas}
            for i, d in enumerate(datas)]


# Cronograma do único módulo já em curso (Prof. Cerejeira): 5 aulas de 10h,
# às quartas-feiras de setembro; as 4 primeiras dadas (40/50h). A última,
# 30/09/2026, fica POR DAR — é a que se reagenda ao vivo para 14/10/2026.
_SESSOES_PY = _sessoes(
    ["02/09/2026", "09/09/2026", "16/09/2026", "23/09/2026", "30/09/2026"], 10, 4
)
# Cinco UFCD já DADAS (concluídas), com datas no passado e 100% das horas.
_SES_ALGO = _sessoes(["03/06/2026", "17/06/2026"], 25, 2)   # 50/50h
_SES_MAT = _sessoes(["04/06/2026", "18/06/2026"], 25, 2)    # 50/50h
_SES_LP = _sessoes(["10/06/2026"], 25, 1)                   # 25/25h
_SES_ETICA = _sessoes(["24/06/2026"], 25, 1)                # 25/25h
_SES_FOLHA = _sessoes(["08/07/2026"], 25, 1)                # 25/25h

# Módulos: (nome, professor, horas_totais, estado, ufcd, [sessoes]).
# Códigos e horas OFICIAIS (plano EGICD). Só os 6 primeiros têm cronograma
# (5 já dadas + Python Avançado em curso); os restantes ficam "pendente",
# listados sem datas (não se inventa calendário de aulas ainda não dadas).
# "" no ufcd = não consta no plano oficial que encontrei (extra do FORAVE).
MODULOS = [
    # Em curso (Cerejeira): última aula 30/09 por dar -> reagenda-se ao vivo p/ 14/10.
    (M_PY_AV, "Luís Cerejeira", 50, "em curso", "10794", _SESSOES_PY),
    # Cinco UFCD já dadas (concluídas).
    ("Conceitos Fundamentais de Programação (Algoritmia)", "Luís Cerejeira", 50, "concluido", "9950", _SES_ALGO),
    ("Matemática", "Nuno Barbosa", 50, "concluido", "5064", _SES_MAT),
    ("Língua Portuguesa - Escrita de Textos", "Ana Teixeira", 25, "concluido", "5143", _SES_LP),
    ("Ética e Deontologia Profissionais", "Stéphanie Dermagne", 25, "concluido", "683", _SES_ETICA),
    ("Folha de Cálculo - Funcionalidades Avançadas", "José Ramalhoto", 25, "concluido", "757", _SES_FOLHA),
    # Restantes: listadas, sem cronograma (ainda não dadas).
    ("Transformação de Dados", "Luís Cerejeira", 25, "pendente", "10800", []),
    ("Gestão e Armazenamento de Dados", "Alberto Pereira", 50, "pendente", "10797", []),
    ("Princípios da Análise Exploratória de Dados", "Carlos Vicente", 25, "pendente", "10807", []),
    ("Programação em Python", "Carlos Vicente", 50, "pendente", "10805", []),
    ("Linguagens de Scripting e Linha de Comandos", "Carlos Vicente", 25, "pendente", "10806", []),
    ("Estatística Aplicada à Gestão", "José Ramalhoto", 50, "pendente", "2166", []),
    ("Engenharia de Software", "Paulo Cunha", 25, "pendente", "5409", []),
    ("Fundamentos de Cibersegurança", "Rui Chilro", 25, "pendente", "9188", []),
    ("Limpeza e Transformação de Dados em Python", "Rui Chilro", 25, "pendente", "10808", []),
    ("Visualização de Dados", "José Ramalhoto", 25, "pendente", "10801", []),
    ("Empresa - Estrutura Organizacional", "Stéphanie Dermagne", 25, "pendente", "7825", []),
    ("Introdução à Proteção de Dados Pessoais", "Stéphanie Dermagne", 25, "pendente", "10672", []),
]

# Turma real (nomes + emails da escola). Todos inscritos no módulo em curso.
# O último é o aluno de demonstração (email real) — persona "aluno" + emails.
_TURMA = [
    ("Ana Silva", "asilvaegicd2527@forave.org"),
    ("Andres Macias", "amaciasegicd2527@forave.org"),
    ("André Moreira", "amoreiraegicd2527@forave.org"),
    ("Cindy Semedo", "csemedoegicd2527@forave.org"),
    ("Cláudio Machado", "cmachadoegicd2527@forave.org"),
    ("Clécia Teixeira", "cteixeiraegicd2527@forave.org"),
    ("Ester Silva", "esilvaegicd2527@forave.org"),
    ("Gabriela Rodrigues", "grodriguesegicd2527@forave.org"),
    ("Ítalo Martins", "imartinsegicd2527@forave.org"),
    ("Jorge Ramos", "jramosegicd2527@forave.org"),
    ("José Martins", "jmartinsegicd2527@forave.org"),
    ("Juliana Nunes", "jnunesegicd2527@forave.org"),
    ("Marcelo Orso", "morsoegicd2527@forave.org"),
    ("Mário Oliveira", "moliveiraegicd2527@forave.org"),
    ("Noemi Martins", "nmartinsegicd2527@forave.org"),
    ("Ricardo Antunes", "rantunesegicd2527@forave.org"),
    ("Rúben Moreira", "rmoreiraegicd2527@forave.org"),
    ("Samuel Silva", "ssilvaegicd2527@forave.org"),
    ("Sérgio Pereira", "spereiraegicd2527@forave.org"),
]

# Alunos (formandos): a turma real + o aluno de demonstração (email real),
# todos inscritos no módulo em curso.
ALUNOS = [(nome, email, [M_PY_AV]) for nome, email in _TURMA]
ALUNOS.append(("Aluno de Demonstração", EMAIL_ALUNO_TESTE, [M_PY_AV]))

# Avaliações do módulo em curso (com pesos -> nota final por média ponderada).
AVALIACOES = {
    M_PY_AV: [
        ("16/09/2026", "Teste", "Teste — POO e estruturas de dados",
         "Avaliar os fundamentos de POO", "Prova escrita", 20),
        ("30/09/2026", "Projeto", "Projeto final",
         "Aplicar tudo num programa real", "Repositório + demonstração", 40),
        ("23/09/2026", "Avaliação contínua", "Avaliação contínua",
         "Empenho, participação e trabalho ao longo do módulo", "—", 40),
    ],
}

# Notas: (módulo, índice da avaliação, email do aluno, nota). Um subconjunto
# da turma + o aluno de demonstração, para o lançamento/pauta terem dados.
# Avaliações: Teste(0), Projeto(1), Participação(2).
NOTAS = [
    (M_PY_AV, 0, "amoreiraegicd2527@forave.org", 16),
    (M_PY_AV, 1, "amoreiraegicd2527@forave.org", 17),
    (M_PY_AV, 2, "amoreiraegicd2527@forave.org", 18),
    (M_PY_AV, 0, "jnunesegicd2527@forave.org", 15),
    (M_PY_AV, 1, "jnunesegicd2527@forave.org", 16),
    (M_PY_AV, 2, "jnunesegicd2527@forave.org", 17),
    (M_PY_AV, 0, "morsoegicd2527@forave.org", 13),
    (M_PY_AV, 1, "morsoegicd2527@forave.org", 14),
    (M_PY_AV, 2, "morsoegicd2527@forave.org", 15),
    (M_PY_AV, 0, "asilvaegicd2527@forave.org", 11),
    (M_PY_AV, 1, "asilvaegicd2527@forave.org", 13),
    (M_PY_AV, 2, "asilvaegicd2527@forave.org", 14),
    (M_PY_AV, 0, "grodriguesegicd2527@forave.org", 17),
    (M_PY_AV, 1, "grodriguesegicd2527@forave.org", 18),
    (M_PY_AV, 2, "grodriguesegicd2527@forave.org", 19),
    (M_PY_AV, 0, EMAIL_ALUNO_TESTE, 14),
    (M_PY_AV, 1, EMAIL_ALUNO_TESTE, 15),
    (M_PY_AV, 2, EMAIL_ALUNO_TESTE, 16),
]


def semear(pasta="dados", engine=None):
    """
    Cria os dados de demo (idempotente, não-destrutivo).

    Com `engine`, semeia na base de dados (SQLite/PostgreSQL); sem ele,
    nos ficheiros JSON da pasta indicada. Os métodos do gestor gravam
    sozinhos, por isso não é preciso guardar no fim.
    """
    gestor = GestorCronograma(pasta_dados=pasta, engine=engine)
    gestor.carregar_dados()  # carrega o que já houver -> só acrescentamos o que falta

    # Professores (registo — o vínculo ao módulo é por nome)
    for nome, email, telefone, modulos in PROFESSORES:
        if gestor.procurar_professor_por_email(email) is None:
            gestor.adicionar_professor(nome, email, telefone, modulos)

    # Módulos. Só se define cronograma (sessões) quando há sessões — os
    # módulos "pendente" ficam sem datas (horas dadas = 0).
    for nome, prof, h_tot, estado, ufcd, sessoes in MODULOS:
        if not gestor.modulo_existe(nome):
            gestor.adicionar_modulo(nome, prof, h_tot, 0, estado, [], ufcd=ufcd)
            if sessoes:
                gestor.editar_modulo(nome, sessoes=sessoes)

    # Alunos (formandos)
    for nome, email, modulos in ALUNOS:
        if not gestor.formando_existe(email):
            gestor.adicionar_formando(nome, email, modulos)

    # Avaliações (só se o módulo ainda não tiver nenhuma -> evita duplicar)
    for modulo_nome, lista in AVALIACOES.items():
        modulo = gestor.procurar_modulo(modulo_nome)
        if modulo is not None and len(modulo.avaliacoes) == 0:
            for data, tipo, desc, obj, deliv, peso in lista:
                gestor.adicionar_avaliacao(modulo_nome, data, tipo, desc, obj, deliv, peso)

    # Notas (lançar sobrescreve -> idempotente)
    for modulo_nome, indice, email, nota in NOTAS:
        gestor.lancar_nota(modulo_nome, indice, email, nota)

    return gestor


def semear_contas(pasta="dados", engine=None):
    """Cria as contas de acesso (coordenador, professor, aluno de demo)."""
    auth = GestorAutenticacao(caminho=os.path.join(pasta, "utilizadores.json"), engine=engine)
    contas = [
        (COORDENADOR, "coordenador"),
        (PROFESSOR_PRINCIPAL, "professor"),
        (EMAIL_ALUNO_TESTE, "aluno"),
    ]
    for email, papel in contas:
        auth.registar(email, PASSWORD_DEMO, papel)  # devolve None se já existir
    return [c[0] for c in contas]


def garantir_env():
    """
    Cria um .env de demo SE ainda não existir (não toca num .env já presente).

    É o que faz o login do coordenador funcionar localmente: o papel é decidido
    por COORDENADOR_EMAILS. Assim a demo fica "à prova de tótos" — sem config manual.
    """
    if os.path.exists(".env"):
        print("  .env já existe — não lhe toquei.")
        print(f"    (Confirma que COORDENADOR_EMAILS inclui {COORDENADOR}.)")
        return
    with open(".env", "w", encoding="utf-8") as f:
        f.write("# .env de DEMONSTRAÇÃO (gerado por seed_demo.py)\n")
        f.write("FONTE_DADOS=json\n")
        f.write(f"COORDENADOR_EMAILS={COORDENADOR}\n")
    print("  Criei um .env de demo (FONTE_DADOS=json + COORDENADOR_EMAILS).")


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "dados"
    print("=" * 56)
    print("  A SEMEAR DADOS DE DEMONSTRAÇÃO (curso EGICD real)")
    print("=" * 56)
    print(f"  Pasta de dados: {pasta}/")

    gestor = semear(pasta)
    emails = semear_contas(pasta)
    garantir_env()

    print()
    print(f"  Módulos:     {len(gestor.modulos)}")
    print(f"  Professores: {len(gestor.professores)}")
    print(f"  Alunos:      {len(gestor.formandos)}")
    print(f"  Contas:      {len(emails)} (password de todas: '{PASSWORD_DEMO}')")
    print()
    print("  ENTRAR:")
    print(f"    Coordenador: {COORDENADOR}")
    print(f"    Professor:   {PROFESSOR_PRINCIPAL}")
    print(f"    Aluno:       {EMAIL_ALUNO_TESTE}  (email real — persona aluno + avisos)")
    print()
    print("  Importar ao vivo: importar_modulos_demo.csv (Inglês Técnico / Ricardo Mendes)")
    print("  Agora corre a WEB:  python app.py    (http://127.0.0.1:5000)")
    print("  ou o TERMINAL:      python main.py")
    print("=" * 56)


if __name__ == "__main__":
    main()
