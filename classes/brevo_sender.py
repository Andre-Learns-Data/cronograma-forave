# ============================================================
# brevo_sender.py — Envio de emails via Brevo (API por HTTP)
# ============================================================
# Porque é que isto existe (em vez de usar só o EmailSender/SMTP):
#
#   Os alojamentos gratuitos na cloud (como o Render) BLOQUEIAM o
#   envio de email por SMTP (a forma "clássica", em que o programa
#   liga directamente ao servidor de correio do Gmail). Fazem-no
#   para travar spam. Resultado: o EmailSender funciona no PC do
#   coordenador, mas NÃO a partir do site alojado.
#
#   A solução da indústria é o "email transaccional por API": em vez
#   de falar SMTP, o programa faz um simples PEDIDO WEB (HTTPS, a
#   mesma "porta" por onde o site já funciona) a um serviço — aqui o
#   Brevo — e é esse serviço que entrega o email. Como é HTTPS e não
#   SMTP, o alojamento não o bloqueia.
#
# Esta classe tem a MESMA interface do EmailSender (atributo
# .configurado + método .enviar(...)), por isso o resto do programa
# pode usar uma ou outra sem saber a diferença ("troca-se a cassete").
#
# Dependências: NENHUMA nova — usa urllib e json, ambos da stdlib.
#   (urllib faz o pedido web; json escreve o corpo no formato que a
#    API do Brevo espera.)
# ============================================================

import json
import urllib.error
import urllib.request


class BrevoSender:
    """
    Envia emails através da API HTTP do Brevo.

    Atributos:
        api_key (str): Chave de API do Brevo (um segredo, como uma password).
        remetente (str): Email de quem envia (tem de estar VERIFICADO no Brevo).
        remetente_nome (str): Nome que aparece como remetente.
        configurado (bool): Se há chave + remetente para poder enviar.
    """

    # Endereço (endpoint) da API do Brevo para enviar um email.
    URL_API = "https://api.brevo.com/v3/smtp/email"

    def __init__(self):
        """Construtor — começa sem credenciais (configura-se depois)."""
        self.api_key = ""
        self.remetente = ""
        self.remetente_nome = "Cronograma FORAVE"
        self.configurado = False

    def configurar(self, api_key, remetente, remetente_nome="Cronograma FORAVE"):
        """
        Define a chave e o remetente.

        Parâmetros:
            api_key (str): Chave de API do Brevo.
            remetente (str): Email remetente (verificado no Brevo).
            remetente_nome (str): Nome a mostrar como remetente.
        """
        self.api_key = api_key
        self.remetente = remetente
        self.remetente_nome = remetente_nome
        # Só está pronto se houver chave E remetente.
        self.configurado = api_key != "" and remetente != ""

    def enviar(self, destinatario_email, destinatario_nome, assunto, corpo,
               reply_to=None):
        """
        Envia um email através do Brevo.

        Mesma assinatura do EmailSender.enviar(), de propósito, para as
        duas classes serem intermutáveis.

        Parâmetros:
            destinatario_email (str): Email do destinatário.
            destinatario_nome (str): Nome do destinatário.
            assunto (str): Assunto do email.
            corpo (str): Texto do email (texto simples).
            reply_to (str|None): Email para onde vai a resposta. O remetente
                continua a ser o institucional (verificado na Brevo); só muda o
                "Responder". Assim as respostas podem ir ter com quem despoletou
                o aviso (ex.: o professor), sem trocar o remetente.

        Retorna:
            bool: True se o Brevo aceitou o email para entrega.
        """
        if not self.configurado:
            print("  Brevo: não configurado — envio ignorado.")
            return False

        # 1. Montar o corpo do pedido no formato que a API espera (dicionário
        #    -> JSON). É como preencher um formulário com remetente, destino,
        #    assunto e texto.
        dados = {
            "sender": {"email": self.remetente, "name": self.remetente_nome},
            "to": [{"email": destinatario_email, "name": destinatario_nome}],
            "subject": assunto,
            "textContent": corpo,
        }
        # "Responder" vai para quem fez a ação (não muda o remetente/sender).
        if reply_to:
            dados["replyTo"] = {"email": reply_to}
        corpo_bytes = json.dumps(dados).encode("utf-8")

        # 2. Construir o pedido HTTP POST, com a chave no cabeçalho "api-key".
        pedido = urllib.request.Request(
            self.URL_API,
            data=corpo_bytes,
            method="POST",
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # 3. Enviar. timeout para nunca ficar "pendurado".
        try:
            with urllib.request.urlopen(pedido, timeout=10) as resposta:
                # A API devolve 201 (Created) quando aceita o email.
                return resposta.status in (200, 201)

        except urllib.error.HTTPError as erro:
            # Erros "esperados" da API (ex.: 401 chave errada, 400 remetente
            # não verificado). Lê-se a explicação para o log.
            detalhe = erro.read().decode("utf-8", "ignore")
            print(f"  Brevo: erro HTTP {erro.code} — {detalhe}")
            return False

        except Exception as erro:
            # Rede em baixo, timeout, etc. Nunca deixar rebentar quem chama.
            print(f"  Brevo: erro inesperado — {erro}")
            return False
