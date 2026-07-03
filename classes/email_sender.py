# ============================================================
# email_sender.py — Envio de emails reais via smtplib
# ============================================================
# Este módulo envia emails reais usando o protocolo SMTP.
# Funciona com Gmail, Outlook, ou qualquer servidor SMTP.
#
# Para Gmail:
#   1. Activar "Verificação em 2 passos" na conta Google
#   2. Criar uma "App Password" em myaccount.google.com
#   3. Usar essa App Password (não a password normal)
#
# IMPORTANTE:
#   - A password NUNCA vai no código — fica num ficheiro .env
#   - O ficheiro .env NUNCA vai para o GitHub
#   - Os emails dos destinatários são dados pessoais (RGPD)
#
# Dependências: nenhuma — smtplib e email são da stdlib
# ============================================================

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    """
    Gere o envio de emails via SMTP.

    Atributos:
        remetente (str): Email de quem envia.
        password (str): App Password do remetente.
        servidor (str): Servidor SMTP (ex: "smtp.gmail.com").
        porta (int): Porta do servidor (normalmente 587).
        configurado (bool): Se as credenciais foram carregadas.
    """

    def __init__(self):
        """
        Construtor — inicializa sem credenciais.

        As credenciais são carregadas depois, a partir
        de um ficheiro .env ou por input do utilizador.
        """
        self.remetente = ""
        self.password = ""
        self.servidor = ""
        self.porta = 587
        self.configurado = False

    # --------------------------------------------------------
    # Configuração
    # --------------------------------------------------------

    def configurar_gmail(self, email, app_password):
        """
        Configura para envio via Gmail.

        Parâmetros:
            email (str): Email Gmail do remetente.
            app_password (str): App Password (não a password normal).
        """
        self.remetente = email
        self.password = app_password
        self.servidor = "smtp.gmail.com"
        self.porta = 587
        self.configurado = True

    def configurar_outlook(self, email, password):
        """
        Configura para envio via Outlook/Hotmail.

        Parâmetros:
            email (str): Email Outlook do remetente.
            password (str): Password da conta.
        """
        self.remetente = email
        self.password = password
        self.servidor = "smtp-mail.outlook.com"
        self.porta = 587
        self.configurado = True

    def carregar_do_env(self, caminho=".env"):
        """
        Carrega as credenciais de um ficheiro .env.

        O ficheiro .env tem o formato:
            EMAIL_REMETENTE=gestor@gmail.com
            EMAIL_PASSWORD=abcd efgh ijkl mnop
            EMAIL_SERVIDOR=smtp.gmail.com
            EMAIL_PORTA=587

        Parâmetros:
            caminho (str): Caminho para o ficheiro .env.

        Retorna:
            bool: True se as credenciais foram carregadas.
        """
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            linhas = ficheiro.readlines()
            ficheiro.close()

            # Percorrer as linhas e extrair os valores
            # Formato: CHAVE=VALOR
            for linha in linhas:
                linha = linha.strip()

                # Ignorar linhas vazias e comentários
                if linha == "" or linha[0] == "#":
                    continue

                # Separar pelo primeiro "="
                # Não usar split("=") porque a password pode ter "="
                posicao_igual = linha.find("=")
                if posicao_igual == -1:
                    continue

                chave = linha[:posicao_igual].strip()
                valor = linha[posicao_igual + 1:].strip()

                if chave == "EMAIL_REMETENTE":
                    self.remetente = valor
                elif chave == "EMAIL_PASSWORD":
                    self.password = valor
                elif chave == "EMAIL_SERVIDOR":
                    self.servidor = valor
                elif chave == "EMAIL_PORTA":
                    self.porta = int(valor)

            # Verificar se todas as credenciais foram carregadas
            if self.remetente != "" and self.password != "" and self.servidor != "":
                self.configurado = True
                print("  Email: credenciais carregadas do .env")
                return True
            else:
                print("  Email: ficheiro .env incompleto.")
                self.configurado = False
                return False

        except FileNotFoundError:
            print(f"  Email: ficheiro '{caminho}' não encontrado.")
            print("  Envio de emails desactivado.")
            self.configurado = False
            return False

    # --------------------------------------------------------
    # Envio
    # --------------------------------------------------------

    def enviar(self, destinatario_email, destinatario_nome, assunto, corpo,
               reply_to=None):
        """
        Envia um email a um destinatário.

        Parâmetros:
            destinatario_email (str): Email do destinatário.
            destinatario_nome (str): Nome do destinatário.
            assunto (str): Assunto do email.
            corpo (str): Texto do email.
            reply_to (str|None): Email para onde vai a resposta do destinatário.
                O remetente continua a ser o institucional (self.remetente); só
                muda o endereço de "Responder". Útil para as respostas irem ter
                com quem despoletou o aviso (ex.: o professor).

        Retorna:
            bool: True se o email foi enviado com sucesso.
        """
        if not self.configurado:
            print("  Email: não configurado — envio ignorado.")
            return False

        try:
            # Construir o email
            # MIMEMultipart permite ter texto + formatação
            msg = MIMEMultipart()
            msg["From"] = self.remetente
            msg["To"] = destinatario_email
            msg["Subject"] = assunto
            if reply_to:
                msg["Reply-To"] = reply_to

            # Adicionar o corpo do email como texto simples
            msg.attach(MIMEText(corpo, "plain", "utf-8"))

            # Ligar ao servidor SMTP
            # starttls() activa a encriptação (segurança)
            # timeout: falha em poucos segundos em vez de ficar "pendurado"
            # (ex.: alojamentos gratuitos que bloqueiam o SMTP de saída — sem
            # timeout, o processo bloquearia até ser morto pelo servidor).
            servidor = smtplib.SMTP(self.servidor, self.porta, timeout=10)
            servidor.starttls()
            servidor.login(self.remetente, self.password)

            # Enviar
            servidor.send_message(msg)
            servidor.quit()

            return True

        except smtplib.SMTPAuthenticationError:
            print("  Email: erro de autenticação — verifica as credenciais.")
            return False

        except smtplib.SMTPException as erro:
            print(f"  Email: erro no envio para {destinatario_email} — {erro}")
            return False

        except Exception as erro:
            print(f"  Email: erro inesperado — {erro}")
            return False

    def enviar_para_todos(self, destinatarios, assunto, corpo):
        """
        Envia o mesmo email a uma lista de destinatários.

        Parâmetros:
            destinatarios (list): Lista de dicts [{"nome": "...", "email": "..."}].
            assunto (str): Assunto do email.
            corpo (str): Texto do email.

        Retorna:
            dict: Resumo com contadores de sucesso e falha.
        """
        if not self.configurado:
            print("  Email: não configurado — envio ignorado.")
            return {"enviados": 0, "falhados": 0}

        enviados = 0
        falhados = 0

        for d in destinatarios:
            sucesso = self.enviar(
                destinatario_email=d["email"],
                destinatario_nome=d["nome"],
                assunto=assunto,
                corpo=corpo
            )

            if sucesso:
                print(f"    ✓ {d['nome']} ({d['email']})")
                enviados = enviados + 1
            else:
                print(f"    ✗ {d['nome']} ({d['email']}) — falhou")
                falhados = falhados + 1

        print(f"\n  Resumo: {enviados} enviados, {falhados} falhados.")

        resultado = {}
        resultado["enviados"] = enviados
        resultado["falhados"] = falhados
        return resultado
