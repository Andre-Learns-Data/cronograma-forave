# Gestor de Cronograma — FORAVE
## Estrutura do Projecto

> Reflete o sistema completo: terminal + **landing pública** + cronograma/áreas
> atrás de login (RGPD) + **3 papéis** (coordenador vê tudo / professor só o seu
> módulo / aluno as suas notas) + **CRUD web completo** (módulos, formandos,
> professores, avaliações, notas) + **importação CSV** (módulos/formandos/
> professores) + **registo de alterações (auditoria)** + **notificações**
> (turma/aluno) + **exportação `.ics` e QR** + **identidade visual FORAVE**.
> **150 testes automáticos.**

---

### Arquitectura — três papéis, uma só lógica

O papel é decidido pelo **email**: **coordenador** (gere tudo), **professor**
(gere só o seu módulo — âmbito/RBAC) e **aluno** (consulta só as suas notas). A
mesma lógica de domínio serve terminal, web e `.exe`.

```
   ESCREVEM (staff, com âmbito)                  CONSULTA (turma)
   ----------------------------                  ----------------
   Coordenador -> todos os módulos               Aluno (login) -> só as
   Professor   -> só o seu módulo                suas notas + calendário
              |                                          ^
    terminal (main.py)  OU  web (app.py)           web (perfil pelo email)
              |                                          |
              v                                          |
     JSON local (dados/)  --opção S-->  Google Sheet -->  Dashboard alojada
     FONTE DE VERDADE      sincroniza   (privado)         (Render, lê do Sheet)
     (offline-first)                                      + landing pública (RGPD)
```

- **Domínio (Python puro):** classes em `classes/`, orquestradas pelo `GestorCronograma`.
- **Persistência local:** JSON em `dados/` (fonte de verdade) + importação CSV.
- **Cloud:** Google Sheet privado (espelho), lido pela dashboard alojada.
- **Interfaces:** terminal + web (Flask) + `.exe` + PWA + QR — a mesma lógica, várias "cascas".
- **Escrita:** no PC pelo terminal (opção **S** sincroniza para o Sheet); no site,
  o **coordenador e o professor** escrevem pela web, gravando de volta no Sheet de
  forma cirúrgica. A **landing** é pública (sem dados); tudo o resto fica atrás de login.

> **Evolução (30/Jun): a web também ESCREVE.** Além de mostrar, o site tem agora
> uma **área de administração** (coordenador e professor, cada um no seu âmbito) que gere módulos, avaliações e
> notas e altera o cronograma — escrevendo de volta no Google Sheet de forma
> **cirúrgica** (só a tab afectada). O acesso é por **papel** (autorização/RBAC):
> a lista `COORDENADOR_EMAILS` define quem é coordenador. Há ainda **recuperação
> de password** por email (token assinado), com envio por **Brevo** (HTTP) no
> alojamento — onde o SMTP está bloqueado — e por Gmail/SMTP localmente.

---

### Mapa de ficheiros

```
Python_projeto_final/
│
├── main.py                          ← App de TERMINAL (coordenador) — python main.py
├── app.py                           ← Dashboard WEB (Flask) — python app.py
│                                       Rotas: público (/, /api/*), aluno (/login,
│                                       /registar, /logout, /aluno), reposição de
│                                       password (/recuperar, /repor/<token>) e
│                                       gestão (/admin, /admin/modulo, /admin/modulo/editar,
│                                       /admin/modulo/datas, /admin/professor, /admin/avaliacao,
│                                       /admin/nota, /admin/alteracao, /admin/importar_csv);
│                                       papéis: coordenador (tudo) / professor (só o seu módulo)
├── gestor_cronograma.py             ← Classe orquestradora — coordena tudo
├── requirements.txt                 ← Dependências (pip install -r requirements.txt)
│
├── classes/                         ← Domínio + integrações (package Python)
│   ├── __init__.py
│   │
│   ├── modulo.py                    ← class Modulo
│   │                                   Atributos: ufcd, nome, professor, horas_totais,
│   │                                   horas_dadas, estado, datas, avaliacoes
│   │                                   Métodos: horas_restantes(), percentagem_concluida(),
│   │                                   esta_concluido(), data_fim_prevista(),
│   │                                   nota_final(email), adicionar_avaliacao(), to_dict()
│   │
│   ├── professor.py                 ← class Professor (nome, email, telefone, modulos)
│   ├── formando.py                  ← class Formando (nome, email, modulos; esta_inscrito())
│   ├── alteracao.py                 ← class Alteracao (mudança de data + motivo + autor)
│   ├── notificacao.py               ← class Notificacao (consola/ficheiro/email)
│   │
│   ├── avaliacao_final.py           ← class Avaliacao
│   │                                   Atributos: data, tipo, descricao, objectivo,
│   │                                   deliverables, peso, notas {email: nota}
│   │                                   Métodos: lancar_nota(), obter_nota(), to_dict()
│   │
│   ├── google_sheets.py             ← class GoogleSheetsSync
│   │                                   conectar(); sincronizar_* (módulos, professores,
│   │                                   formandos, alterações, avaliações, NOTAS);
│   │                                   obter_* (leitura); acrescentar_utilizador();
│   │                                   atualizar_password_utilizador() (reposição);
│   │                                   acrescentar_auditoria()/obter_auditoria() (append-only)
│   │
│   ├── carregador_sheets.py         ← gestor_a_partir_de_sheets()
│   │                                   reconstrói o GestorCronograma a partir do Sheet
│   │                                   (usado quando o dashboard está alojado)
│   │
│   ├── email_sender.py              ← class EmailSender (envio por SMTP — local)
│   ├── brevo_sender.py              ← class BrevoSender (envio por API HTTP —
│   │                                   alojamento; mesma interface do EmailSender)
│   ├── importador_csv.py            ← class ImportadorCSV (importação em massa)
│   │
│   ├── utilizador.py                ← class Utilizador (email, password_hash, papel)
│   ├── autenticacao.py              ← class GestorAutenticacao
│   │                                   registar()/autenticar() com hash (werkzeug);
│   │                                   reposição de password (token itsdangerous:
│   │                                   criar/validar_token, redefinir_password);
│   │                                   backend JSON local OU Google Sheet
│   │
│   ├── auditoria.py                 ← class RegistoAuditoria
│   │                                   registo append-only "quem/o quê/quando" das
│   │                                   escritas da admin (accountability); to_dict/from_dict
│   │
│   ├── insights_engine.py           ← class InsightsEngine (indicadores do dashboard)
│   ├── gerador_qr.py                ← gerar_qr(url, caminho) — QR code PNG
│   ├── gerador_ics.py               ← gerar_ics(modulos) — cronograma em iCalendar (.ics)
│   └── utils.py                     ← Funções de terminal (menus, inputs, escolher_da_lista)
│
├── templates/                       ← HTML da dashboard (Flask + Jinja)
│   ├── landing.html                 ← Página inicial PÚBLICA (boas-vindas + 3 perfis;
│   │                                   sem dados do curso — RGPD)
│   ├── dashboard.html               ← Cronograma (/cronograma) — só AUTENTICADO
│   │                                   (módulos, progresso, gráfico, PDF)
│   ├── login.html                   ← Login (aluno/professor/coordenador) + "esqueci-me"
│   ├── registar.html                ← Auto-registo (aluno/professor/coordenador)
│   ├── aluno.html                   ← Área pessoal (notas + nota final UFCD)
│   ├── recuperar.html               ← Pedir reposição de password (email)
│   ├── repor.html                   ← Definir nova password (a partir do link)
│   └── admin.html                   ← Gestão: coordenador (tudo) / professor (só o seu):
│                                       módulos/avaliações/notas; cronograma; professores
│
├── static/                          ← PWA (torna a dashboard instalável)
│   ├── manifest.json                ← Definições da "app"
│   ├── sw.js                        ← Service worker (cache; nunca guarda dados pessoais)
│   ├── icon-192.png / icon-512.png  ← Ícones
│
├── testes/                          ← Bateria de testes (unittest) — 150 testes
│   ├── fakes.py                     ← Dublês do Google Sheets (sem rede)
│   ├── test_dominio.py              ← Modulo, Avaliacao, Formando
│   ├── test_gestor.py               ← CRUD, notas, RGPD, persistência
│   ├── test_importador_csv.py       ← Importação CSV
│   ├── test_autenticacao.py         ← Login + reposição de password (JSON e Sheet)
│   ├── test_sheets.py               ← Round-trip gestor → Sheet → reconstrução
│   │                                   + auditoria append-only (tab "Auditoria")
│   ├── test_brevo.py                ← Envio Brevo (pedido HTTP, sem rede)
│   ├── test_ics.py                  ← Exportação iCalendar (.ics) do cronograma
│   └── test_web.py                  ← Rotas Flask: landing pública + tudo atrás de
│                                       login (RGPD), 3 papéis (coordenador/professor/
│                                       aluno), CRUD web (módulos/formandos/professores/
│                                       avaliações/notas), notificações, auditoria, .ics
│
├── DEPLOY.md                        ← Guia de alojamento no Render
├── Procfile                         ← Comando de arranque (gunicorn app:app)
├── runtime.txt                      ← Versão de Python para o Render
├── render.yaml                      ← Blueprint de configuração do Render
│
├── .env.example                     ← Template de configuração — copiar para .env
├── .env                             ← Credenciais reais (NÃO vai para o GitHub)
├── credentials.json                 ← Credenciais Google (NÃO vai para o GitHub)
├── .gitignore                       ← Protege ficheiros sensíveis
├── README.md                        ← Documentação principal
├── DEMO.md / DEMO.html / DEMO.pdf    ← Guião de demonstração
├── seed_demo.py                     ← Carrega dados de demonstração
├── LICENSE                          ← Licença (MIT)
│
└── dados/                           ← Criada automaticamente (NÃO vai para o GitHub)
    ├── modulos.json                 ← Módulos (com avaliações e notas embutidas)
    ├── professores.json
    ├── formandos.json               ← Emails — RGPD
    ├── alteracoes.json
    ├── notificacoes.json
    ├── utilizadores.json            ← Contas de aluno (hash da password) — local
    └── auditoria.json               ← Registo de auditoria da admin (modo local)
```

---

### Relações entre classes

```
                    ┌─────────────────────────┐
                    │    GestorCronograma      │
                    │  modulos[] professores[] │
                    │  formandos[] alteracoes[]│
                    │  notificacoes[]          │
                    └──────────┬──────────────┘
                               │
        ┌────────┬────────┬────┴────┬──────────┬───────────┐
        ▼        ▼        ▼         ▼          ▼           ▼
     Modulo    Prof   Formando  Alteracao  Notificacao   (JSON)
       │
       └── avaliacoes[] ──► Avaliacao ──► notas {email: nota}

   Camada web (separada):
     GestorAutenticacao ──► Utilizador (email, hash, papel)
                        └──► reposição de password (token itsdangerous)
     InsightsEngine ──► lê do GestorCronograma
     carregador_sheets ──► constrói GestorCronograma a partir do Sheet
     EmailSender / BrevoSender ──► mesma interface .enviar() (SMTP local / HTTP alojado)
     Autorização: COORDENADOR_EMAILS → papel "coordenador" → área /admin (RBAC)
```

---

### Fluxo 1 — o coordenador lança uma nota (terminal)

```
  Coordenador → main.py opção 13
       │
       ▼
  Escolhe módulo → avaliação → nota (0-20) de cada formando inscrito
       │
       ▼
  GestorCronograma.lancar_nota() → Avaliacao.lancar_nota() → guarda JSON
       │
       ▼
  Modulo.nota_final(email) calcula a média ponderada pelos pesos
       │
       ▼
  Opção S → sincroniza para o Google Sheet (tabs Avaliações + Notas)
```

### Fluxo 2 — o aluno vê as notas (web alojada)

```
  Aluno → site → "Registar" (email tem de estar na lista de formandos)
       │  password guardada em HASH (nunca em texto)
       ▼
  "Entrar" → sessão criada
       │
       ▼
  /aluno → carrega o gestor a partir do Google Sheet (carregador_sheets)
       │
       ▼
  Mostra SÓ os dados deste aluno: módulos, avaliações, a sua nota,
  e a nota final por UFCD                              (RGPD)
```

### Fluxo 3 — o coordenador gere pela web (área de administração)

```
  Coordenador → site → "Entrar" (email está em COORDENADOR_EMAILS)
       │  papel "coordenador" → acesso a /admin (autorização/RBAC)
       ▼
  /admin → vê TUDO (todas as notas) e gere:
       ├─ adicionar módulo / avaliação · lançar notas
       └─ alterar o cronograma (mudar data) + avisar a turma por email
       │
       ▼
  Escrita CIRÚRGICA: grava só a tab afectada no Google Sheet
  (sincronizar_modulos / _avaliacoes / _notas / _alteracoes) e invalida a cache
       │
       ▼
  AUDITORIA: cada escrita acrescenta uma linha à tab "Auditoria"
  (quem · o quê · quando · detalhe — nas notas, email=valor) — append-only
       │
       ▼
  "uma lógica de domínio, dois canais de escrita": terminal E web
```

### Fluxo 4 — o aluno recupera a password ("esqueci-me")

```
  Aluno → /recuperar (escreve o email)
       │  resposta sempre neutra (não revela quem tem conta)
       ▼
  token assinado (itsdangerous) → link enviado por email
  (Brevo no alojamento · Gmail/SMTP local)
       │
       ▼
  /repor/<token> → valida (assinatura + validade + uso único) → nova password
```

---

### Setup rápido (local)

```
1. pip install -r requirements.txt
2. cp .env.example .env   (e preencher)
3. Terminal:  python main.py
   Dashboard: python app.py   →  http://127.0.0.1:5000
```

Alojamento na internet: ver `DEPLOY.md`.

---

### Ficheiros que NÃO vão para o GitHub (.gitignore)

```
  .env                      → Passwords e credenciais
  credentials.json          → Credenciais da API do Google
  dados/                    → JSON com dados pessoais (RGPD) e contas
```

---

### Tecnologias utilizadas

```
  Python 3                 → Linguagem principal (POO, dicts, ficheiros, try/except)
  json / datetime / os     → stdlib (persistência, datas, sistema)
  smtplib / email.mime     → stdlib (envio de emails por SMTP — local)
  urllib                   → stdlib (envio de emails por HTTP via Brevo — alojamento)
  Flask                    → Dashboard web
  gunicorn                 → Servidor de produção (no Render)
  gspread / google-auth    → Google Sheets API
  werkzeug.security        → Hash de passwords (vem com o Flask)
  itsdangerous             → Tokens assinados de reposição de password (vem com Flask)
  Brevo (API HTTP)         → Email transacional no alojamento (Render bloqueia SMTP)
  reportlab                → Exportação PDF
  qrcode / Pillow          → QR codes e ícones do PWA
  datetime (iCalendar)     → Exportação .ics do cronograma (stdlib, sem dependências)
```
