# ============================================================
# seed_demo.py — Semeia DADOS DE DEMONSTRAÇÃO
# ============================================================
# Enche o sistema com um curso de demonstração (módulos, professores,
# alunos, avaliações e notas) e cria as contas de acesso — tudo num só
# comando, para a demo estar pronta em segundos.
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
#   - Coordenador: chronosforave@gmail.com   (vê/gere tudo)
#   - Professor:   luis.cerejeira@forave.pt    (vê só o módulo dele)
#   - 4 alunos     (veem só as suas notas)
#
# NÃO usar dados reais aqui — é só demonstração.
# ============================================================

import os
import sys

from classes.autenticacao import GestorAutenticacao
from gestor_cronograma import GestorCronograma

# ------------------------------------------------------------
# Conteúdo da demonstração (CET Gestão de Informação e Ciência de Dados)
# ------------------------------------------------------------
PASSWORD_DEMO = "demo1234"
COORDENADOR = "chronosforave@gmail.com"
PROFESSOR_PRINCIPAL = "luis.cerejeira@forave.pt"

# Professores: (nome, email, telefone, [módulos que gere])
PROFESSORES = [
    ("Luís Cerejeira", PROFESSOR_PRINCIPAL, "", ["Programação Avançada com Python"]),
    ("Rita Fonseca", "rita.fonseca@forave.pt", "", ["Fundamentos de Bases de Dados"]),
    ("Miguel Santos", "miguel.santos@forave.pt", "", ["Análise e Visualização de Dados"]),
]

def _sessoes(datas, horas_cada, n_dadas):
    """
    Constrói a lista de sessões de um módulo para o seed.

    Cada aula fica com `horas_cada` horas; as primeiras `n_dadas` ficam
    marcadas como "dadas" (é essa marca que soma às horas dadas do módulo).
    """
    return [{"data": d, "horas": horas_cada, "realizada": i < n_dadas}
            for i, d in enumerate(datas)]


# Módulos: (nome, professor, horas_totais, estado, ufcd, [sessoes]).
# As horas DADAS já não se escrevem à mão — são a soma das aulas marcadas
# como dadas (ver _sessoes). Ex.: Python = 5 aulas de 10h, 3 dadas -> 30/50h.
MODULOS = [
    ("Programação Avançada com Python", "Luís Cerejeira", 50, "em curso", "10794",
     _sessoes(["02/06/2026", "09/06/2026", "16/06/2026", "23/06/2026", "30/06/2026"], 10, 3)),
    ("Fundamentos de Bases de Dados", "Rita Fonseca", 40, "concluido", "",
     _sessoes(["05/05/2026", "12/05/2026", "19/05/2026", "26/05/2026"], 10, 4)),
    ("Análise e Visualização de Dados", "Miguel Santos", 40, "em curso", "",
     _sessoes(["07/07/2026", "14/07/2026", "21/07/2026", "28/07/2026"], 10, 1)),
]

# Aluno de TESTE com email REAL, para verificar a receção dos emails
# automáticos (nota individual / reagendamento). O nome é fictício; o email
# é uma caixa de correio de teste (a password dessa caixa NÃO fica aqui —
# não é precisa: o programa só usa o endereço como destinatário).
EMAIL_ALUNO_TESTE = "alunoforavecetdados@gmail.com"

# Alunos: (nome, email, [módulos em que está inscrito]) — nomes fictícios.
# O último é o aluno de TESTE (email real acima).
ALUNOS = [
    ("Sofia Marques", "sofia.marques@forave.pt",
     ["Programação Avançada com Python", "Fundamentos de Bases de Dados"]),
    ("Tiago Fernandes", "tiago.fernandes@forave.pt",
     ["Programação Avançada com Python", "Fundamentos de Bases de Dados"]),
    ("Inês Rocha", "ines.rocha@forave.pt",
     ["Programação Avançada com Python", "Análise e Visualização de Dados"]),
    ("Rui Teixeira", EMAIL_ALUNO_TESTE,
     ["Programação Avançada com Python"]),
]

# Avaliações por módulo: (data, tipo, descrição, objectivo, deliverables, peso)
AVALIACOES = {
    "Programação Avançada com Python": [
        ("16/06/2026", "Teste", "Teste 1 — POO e estruturas de dados",
         "Avaliar os fundamentos de POO", "Prova escrita", 30),
        ("23/06/2026", "Projeto", "Projeto final",
         "Aplicar tudo num programa real", "Repositório + demonstração", 50),
        ("23/06/2026", "Avaliação contínua", "Participação nas aulas",
         "Empenho e participação", "—", 20),
    ],
    "Fundamentos de Bases de Dados": [
        ("19/05/2026", "Teste", "Teste global",
         "Modelo relacional e SQL", "Prova escrita", 100),
    ],
}

# Notas: (módulo, índice da avaliação, email do aluno, nota)
_PAP = "Programação Avançada com Python"
_BD = "Fundamentos de Bases de Dados"
NOTAS = [
    # Programação Avançada com Python: Teste(0), Projeto(1), Participação(2)
    (_PAP, 0, "sofia.marques@forave.pt", 16),
    (_PAP, 1, "sofia.marques@forave.pt", 17),
    (_PAP, 2, "sofia.marques@forave.pt", 18),
    (_PAP, 0, "tiago.fernandes@forave.pt", 12),
    (_PAP, 1, "tiago.fernandes@forave.pt", 14),
    (_PAP, 2, "tiago.fernandes@forave.pt", 15),
    (_PAP, 0, "ines.rocha@forave.pt", 9),
    (_PAP, 1, "ines.rocha@forave.pt", 11),
    (_PAP, 2, "ines.rocha@forave.pt", 13),
    (_PAP, 0, EMAIL_ALUNO_TESTE, 14),
    (_PAP, 1, EMAIL_ALUNO_TESTE, 15),
    (_PAP, 2, EMAIL_ALUNO_TESTE, 16),
    # Fundamentos de Bases de Dados: Teste(0)
    (_BD, 0, "sofia.marques@forave.pt", 15),
    (_BD, 0, "tiago.fernandes@forave.pt", 13),
]


def semear(pasta):
    """Cria os dados de demo na pasta indicada (idempotente, não-destrutivo)."""
    gestor = GestorCronograma(pasta_dados=pasta)
    gestor.carregar_dados()  # carrega o que já houver -> só acrescentamos o que falta

    # Professores (registo — o vínculo ao módulo é por nome e por esta lista)
    for nome, email, telefone, modulos in PROFESSORES:
        if gestor.procurar_professor_por_email(email) is None:
            gestor.adicionar_professor(nome, email, telefone, modulos)

    # Módulos (com sessões: data + horas + "dada"). As horas dadas resultam
    # da soma das aulas marcadas como dadas (definir_sessoes, via editar_modulo).
    for nome, prof, h_tot, estado, ufcd, sessoes in MODULOS:
        if not gestor.modulo_existe(nome):
            gestor.adicionar_modulo(nome, prof, h_tot, 0, estado, [], ufcd=ufcd)
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


def semear_contas(pasta):
    """Cria as contas de acesso (coordenador, professor, alunos)."""
    auth = GestorAutenticacao(caminho=os.path.join(pasta, "utilizadores.json"))
    contas = [(COORDENADOR, "coordenador")]
    contas.append((PROFESSOR_PRINCIPAL, "professor"))
    for _nome, email, _modulos in ALUNOS:
        contas.append((email, "aluno"))
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
    print("  A SEMEAR DADOS DE DEMONSTRAÇÃO")
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
    print("    Alunos:      sofia.marques@forave.pt · tiago.fernandes@forave.pt · ines.rocha@forave.pt")
    print(f"    Aluno TESTE: {EMAIL_ALUNO_TESTE}  (email real — verifica aqui os avisos automáticos)")
    print()
    print("  Agora corre a WEB:  python app.py    (http://127.0.0.1:5000)")
    print("  ou o TERMINAL:      python main.py")
    print("=" * 56)


if __name__ == "__main__":
    main()
