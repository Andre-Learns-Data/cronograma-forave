# ============================================================
# token_aluno.py — Tokens assinados para o .ics do ALUNO
# ============================================================
# A área do aluno tem um QR code para ele levar o SEU calendário
# (só os módulos em que está inscrito) para o telemóvel. O problema
# é o mesmo do QR por módulo: a câmara do telemóvel abre o link SEM
# a sessão iniciada, e os dados do aluno vivem atrás de login (RGPD).
#
# Para o QR funcionar sem partir essa regra, o link leva um TOKEN
# ASSINADO que carrega o EMAIL do aluno:
#
#   - assinado com a chave secreta da aplicação -> ninguém o falsifica;
#   - temporizado (URLSafeTimedSerializer) -> expira sozinho (30 dias);
#   - só o próprio aluno, já autenticado, viu o QR e o gerou.
#
# É exactamente a mesma técnica do token por módulo (token_modulo.py)
# e dos tokens de reposição de password (autenticacao.py), aqui
# reutilizada para "abrir" o .ics pessoal de um aluno. Nada é guardado
# em disco — o próprio token é a prova (ideal para disco efémero,
# ex.: Render).
#
# Nota RGPD: o token só dá acesso ao .ics (datas de aulas/avaliações
# dos módulos do aluno) — NÃO às notas. As notas continuam só na área
# autenticada. O .ics não é sensível; o filtro por aluno é de comodidade
# (vê só o que lhe interessa), não um segredo.
#
# Só usa o itsdangerous, que já vem com o Flask — sem dependências novas.
#
# Criado na: afinação final da demo (área do aluno — QR -> .ics do aluno)
# ============================================================

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# "Sal" próprio deste tipo de token. Isola-o dos restantes tokens
# assinados com a mesma chave (módulo usa "modulo-ics", reposição de
# password usa outro): um token de um tipo nunca é aceite como de outro.
_SALT = "aluno-ics"

# Validade por defeito: 30 dias (igual ao QR por módulo). Um QR mostrado
# num ecrã durante a defesa, ou guardado pelo aluno, continua a abrir
# durante um mês; passado esse tempo, basta recarregar a área do aluno
# para gerar um novo.
VALIDADE_PADRAO_SEGUNDOS = 30 * 24 * 60 * 60  # 2 592 000 s


def _serializador(secret):
    """Cria o serializador assinado/temporizado para os tokens de aluno."""
    return URLSafeTimedSerializer(secret, salt=_SALT)


def criar_token_aluno(email, secret):
    """
    Gera um token assinado que representa UM aluno (pelo email).

    Parâmetros:
        email (str): Email do aluno (a chave única no sistema).
        secret (str): A chave secreta da aplicação (app.secret_key).

    Retorna:
        str: O token assinado, seguro para viajar dentro de um URL/QR.
    """
    return _serializador(secret).dumps(email)


def validar_token_aluno(token, secret, validade_segundos=VALIDADE_PADRAO_SEGUNDOS):
    """
    Verifica um token de aluno e devolve o email que ele carrega.

    Falha (devolve None) se o token estiver corrompido/falsificado, tiver
    sido assinado com outra chave, ou tiver expirado.

    Parâmetros:
        token (str): O token vindo do link/QR.
        secret (str): A chave secreta da aplicação (app.secret_key).
        validade_segundos (int): Tempo de validade. Por defeito, 30 dias.

    Retorna:
        str ou None: O email do aluno se o token for válido, senão None.
    """
    try:
        return _serializador(secret).loads(token, max_age=validade_segundos)
    except (BadSignature, SignatureExpired):
        return None
