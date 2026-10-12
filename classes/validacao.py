# ============================================================
# validacao.py — Validações de formato partilhadas
# ============================================================
# Funções puras de validação, usadas tanto pela web (app.py) como
# pela importação de CSV (importador_csv.py). Ficam fora do domínio
# porque são regras de FORMATO (não de negócio) e não imprimem nada
# — devolvem True/False (separação de responsabilidades, secção 5.4).
#
# Alinhado com: Aula 6 (strings e condições).
# ============================================================


def email_valido(email):
    """
    Verifica se um email tem um formato minimamente válido.

    Não valida a RFC inteira (seria exagero para o contexto) — garante
    só o essencial que apanha os erros reais: exactamente um '@', com
    texto antes, e um domínio com um ponto no meio, sem espaços. Serve
    para travar lixo como "abc" ou "sem-arroba" antes de entrar no
    sistema — tanto no formulário como na importação de CSV.

    Até aqui a validação de formato existia só no browser (campos
    type="email"); um POST directo ou um CSV contornavam-na. Esta
    função fecha essa porta do lado do servidor.

    Parâmetros:
        email (str): o endereço a verificar.

    Retorna:
        bool: True se o formato é aceitável, False caso contrário.
    """
    # Proteger contra None (ex.: célula de CSV em branco)
    if email is None:
        return False

    texto = email.strip()

    # Não pode estar vazio nem ter espaços
    if texto == "" or " " in texto:
        return False

    # Tem de ter exactamente um '@'
    if texto.count("@") != 1:
        return False

    # Separar a parte local do domínio
    local, dominio = texto.split("@")

    # Texto antes do '@' e um domínio não vazio
    if local == "" or dominio == "":
        return False

    # O domínio tem de ter um ponto no meio (ex.: forave.pt), nunca na ponta
    if "." not in dominio:
        return False
    if dominio.startswith(".") or dominio.endswith("."):
        return False

    return True
