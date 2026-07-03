# Guia de Deploy — Dashboard FORAVE no Render (Fase C)

Este guia põe a dashboard **online**, para a turma toda lhe aceder com login.
O **programa de terminal continua a funcionar local, sem nada disto** — isto é só
para a versão alojada na internet.

> **Como funciona, em duas linhas:** o coordenador escreve no terminal → sincroniza
> para o Google Sheet privado (opção `S`) → o site alojado lê do Sheet. As contas dos
> alunos também ficam no Sheet (tab "Utilizadores"), por isso sobrevivem a reinícios.

---

## 0. Pré-requisitos (já tens)

- [x] `credentials.json` da Service Account (Sessão 2).
- [x] A spreadsheet partilhada com o email da Service Account (Editor).
- [x] O `.env` local com `GOOGLE_SHEETS_NOME` (ID da spreadsheet) e `GOOGLE_SHEETS_CREDENCIAIS`.
- [ ] Dados no Sheet: corre `python main.py`, adiciona/importa módulos+formandos, e usa a
      opção **S (Sincronizar)** para os enviar para o Sheet. (Sem dados, o site abre vazio.)

---

## 1. Enviar o código para o GitHub

O Render instala a partir de um repositório GitHub, por isso é preciso fazer push:

```bash
git push origin main
```

> Lembra-te: o `push` é **só** para o alojamento. O `credentials.json`, o `.env` e a
> pasta `dados/` **não** vão (estão no `.gitignore`) — as credenciais entram no Render
> de forma segura (passo 4).

---

## 2. Criar o serviço no Render

1. Cria conta grátis em https://render.com (podes entrar com o GitHub).
2. **New +** → **Web Service** → liga o repositório `Python_projeto_final`.
3. O Render deteta o `render.yaml` e pré-preenche quase tudo:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: **Free**

---

## 3. Variáveis de ambiente

No painel do serviço → **Environment**. O `render.yaml` já define:

| Variável | Valor | Notas |
|---|---|---|
| `FONTE_DADOS` | `sheets` | faz o site ler do Google Sheet |
| `FLASK_SECRET_KEY` | (gerado pelo Render) | chave de sessão — deixa o Render gerar |
| `GOOGLE_SHEETS_NOME` | **(preencher)** | o **ID** da tua spreadsheet (o mesmo do `.env`) |
| `GOOGLE_SHEETS_CREDENCIAIS` | `/etc/secrets/credentials.json` | caminho do ficheiro do passo 4 |

Só tens de preencher o **`GOOGLE_SHEETS_NOME`** (cola o ID da spreadsheet).

### Email (para a recuperação de password funcionar) — via Brevo

A funcionalidade "Esqueci-me da password" envia um link por email. **No Render
gratuito não dá para usar o Gmail/SMTP** — a plataforma bloqueia o envio por SMTP
(portas 25/465/587) desde Setembro/2025, para travar spam. A solução é enviar o
email por uma **API HTTP** (que o Render não bloqueia): usamos o **Brevo**
(plano gratuito, ~300 emails/dia, sem cartão).

Passos (uma vez):

1. Cria conta grátis em https://www.brevo.com
2. **Verifica o remetente:** no Brevo, **Senders & IP** → **Senders** → adiciona o
   `chronosforave@gmail.com` e confirma o email de verificação que recebes.
3. Gera a chave: **SMTP & API** → **API Keys** → **Generate a new API key** → copia
   o valor (começa por `xkeysib-...`).
4. No Render → **Environment**, acrescenta:

| Variável | Valor | Notas |
|---|---|---|
| `BREVO_API_KEY` | a chave `xkeysib-...` | **segredo** — trata como uma password |
| `EMAIL_REMETENTE` | `chronosforave@gmail.com` | tem de ser o remetente **verificado** no Brevo |

O site escolhe sozinho: **se houver `BREVO_API_KEY`, usa o Brevo** (HTTP); senão,
tenta o Gmail/SMTP (que só funciona no PC do coordenador, não no Render).

Sem nada disto o site **não rebenta**: a página de recuperação continua a
funcionar e mostra a mensagem neutra, mas o email não é enviado (o link fica
registado no log do servidor, para o coordenador poder ajudar manualmente).

> **Local (PC do coordenador):** continua a usar o Gmail/SMTP via `.env`
> (`EMAIL_REMETENTE` + `EMAIL_PASSWORD`). Para testar o Brevo localmente, podes
> pôr `BREVO_API_KEY=...` no `.env`.

### Acesso de coordenador (área de administração)

A área `/admin` (gerir módulos/avaliações/notas pela web) é reservada a
**coordenadores**. Quem é coordenador define-se por uma lista de emails de
confiança — **não** se ganha pelo registo (segurança):

| Variável | Valor | Notas |
|---|---|---|
| `COORDENADOR_EMAILS` | emails separados por vírgula | ex: `chronosforave@gmail.com` |

Quem estiver nesta lista, ao iniciar sessão, entra como coordenador (mesmo que
a conta no Sheet diga "aluno"); todos os outros são alunos. Um email de
coordenador pode registar-se na mesma (não precisa de estar na lista de
formandos). **Localmente** põe-se a mesma variável no `.env`.

---

## 4. Carregar o credentials.json como Secret File

No painel do serviço → **Environment** → **Secret Files** → **Add Secret File**:

- **Filename:** `credentials.json`
- **Contents:** cola todo o conteúdo do teu `credentials.json`

O Render disponibiliza-o em `/etc/secrets/credentials.json` (é o caminho que pusemos
na variável `GOOGLE_SHEETS_CREDENCIAIS`). Assim a chave nunca anda no GitHub.

---

## 5. Publicar

Carrega em **Create Web Service** / **Deploy**. Ao fim de 1-2 minutos tens um URL tipo:

```
https://cronograma-forave.onrender.com
```

> **Plano grátis:** o serviço "adormece" após ~15 min sem visitas; o primeiro acesso a
> seguir demora ~50s a acordar. Normal — depois fica rápido. O Render dá **HTTPS**
> automático, por isso o PWA fica instalável no telemóvel.

---

## 6. Testar online

1. Abre o URL → vês o cronograma público (módulos, progresso, avaliações).
2. **Registar** → usa um email que esteja na lista de formandos do Sheet → define password.
   (A tab "Utilizadores" é criada automaticamente no primeiro registo.)
3. **Entrar** → vês a tua área com as tuas notas e a nota final por UFCD.
4. Gera o **QR** para este URL: no terminal, opção **14**, e cola o URL do Render.
   Imprime o QR ou põe-no no slide — quem o lê abre o sistema no telemóvel.

---

## 7. Fluxo do dia-a-dia (depois de alojado)

1. Coordenador abre `python main.py` (local), adiciona/edita dados, lança notas (opção 13).
2. Opção **S** → sincroniza tudo para o Sheet (módulos, avaliações, **notas**).
3. O site alojado reflete as mudanças no próximo acesso (cache de 30s).

---

## Resolução de problemas

| Sintoma | Verificar |
|---|---|
| Site abre vazio | Há dados no Sheet? Fizeste a opção **S** no terminal? |
| Erro de ligação ao Google | `GOOGLE_SHEETS_NOME` certo? Secret File `credentials.json` carregado? Spreadsheet partilhada com a Service Account? |
| Não consigo registar | O email está na lista de formandos (e foi sincronizado para o Sheet)? |
| Login não persiste após redeploy | Confirma `FONTE_DADOS=sheets` (as contas têm de estar no Sheet, não em disco) |
| Primeiro acesso muito lento | Normal no plano grátis (cold start ~50s); o seguinte é rápido |

---

## RGPD (lembrete)

- A spreadsheet é **privada** (só partilhada com a Service Account) — **nunca a publiques**.
- As notas só são visíveis ao próprio aluno autenticado; o service worker nunca as guarda em cache.
- O direito ao apagamento está na opção 12 do terminal (remover formando).
