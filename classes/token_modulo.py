# ============================================================
# token_modulo.py — Tokens assinados para o .ics de um módulo
# ============================================================
# Um QR code por módulo aponta para o .ics DESSE módulo. O problema:
# a câmara do telemóvel abre o link SEM a sessão iniciada, e os dados
# do curso vivem atrás de login (decisão RGPD). Para o QR funcionar
# sem partir essa regra, o link leva um TOKEN ASSINADO:
#
#   - assinado com a chave secreta da aplicação -> ninguém o falsifica;
#   - temporizado (URLSafeTimedSerializer) -> expira sozinho (30 dias);
#   - só quem estava autenticado no dashboard viu o QR e o gerou.
#
# É exactamente a mesma técnica dos tokens de reposição de password
# (ver classes/autenticacao.py), aqui reutilizada para "abrir" o .ics
# de um módulo específico. Nada é guardado em disco — o próprio token
# é a prova (ideal para alojamento com disco efémero, ex: Render).
#
# Só usa o itsdangerous, que já vem com o Flask — sem dependências novas.
#
# Criado na: Bloco 4 / Fase D (wow factors — QR por módulo -> .ics)
# ============================================================

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# "Sal" próprio deste tipo de token. Isola-o dos outros tokens assinados
# com a mesma chave (ex.: reposição de password usa "reposicao-password"):
# um token de um tipo nunca é aceite como token de outro tipo.
_SALT = "modulo-ics"

# Validade por defeito: 30 dias. Um QR num cartaz/slide continua a
# funcionar durante um mês; passado esse tempo, deixa de abrir (basta
# recarregar a página do dashboard para gerar um novo).
VALIDADE_PADRAO_SEGUNDOS = 30 * 24 * 60 * 60  # 2 592 000 s


def _serializador(secret):
    """Cria o serializador assinado/temporizado para os tokens de módulo."""
    return URLSafeTimedSerializer(secret, salt=_SALT)


def criar_token_modulo(nome_modulo, secret):
    """
    Gera um token assinado que representa UM módulo (pelo nome).

    Parâmetros:
        nome_modulo (str): Nome do módulo (a chave única no sistema).
        secret (str): A chave secreta da aplicação (app.secret_key).

    Retorna:
        str: O token assinado, seguro para viajar dentro de um URL/QR.
    """
    return _serializador(secret).dumps(nome_modulo)


def validar_token_modulo(token, secret, validade_segundos=VALIDADE_PADRAO_SEGUNDOS):
    """
    Verifica um token de módulo e devolve o nome do módulo que ele carrega.

    Falha (devolve None) se o token estiver corrompido/falsificado, tiver
    sido assinado com outra chave, ou tiver expirado.

    Parâmetros:
        token (str): O token vindo do link/QR.
        secret (str): A chave secreta da aplicação (app.secret_key).
        validade_segundos (int): Tempo de validade. Por defeito, 30 dias.

    Retorna:
        str ou None: O nome do módulo se o token for válido, senão None.
    """
    try:
        return _serializador(secret).loads(token, max_age=validade_segundos)
    except (BadSignature, SignatureExpired):
        return None
