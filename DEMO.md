# Guião de Demonstração — Gestor de Cronograma FORAVE

Este documento descreve, passo a passo, como demonstrar as funcionalidades do
sistema. Está organizado por **perfil de utilizador** (Coordenador, Professor e
Aluno), numa sequência lógica: o Coordenador prepara o curso, o Professor gere o
seu módulo e lança notas, e o Aluno consulta os seus resultados.

Para além de *o que* fazer, o guião explica também *porquê* as coisas estão feitas
como estão — para dar uma noção da estratégia e das decisões de engenharia à medida
que se percorre a demonstração. Cada passo usa três registos visuais:

- **Passo numerado** — a ação a realizar (o que clicar/escrever).

!!! resultado "Resultado esperado"
    O que se deve ver no ecrã depois da ação (caixa verde).

!!! porque "Porquê / RGPD / Nos bastidores"
    Comentário: a decisão de design, a escolha de privacidade ou um detalhe de
    como funciona por baixo (caixa azul). É opcional — pode ler-se ou saltar-se
    sem perder o fio dos passos.

> **Contas para a demonstração**
>
> | Perfil | Email | Password |
> |---|---|---|
> | Coordenador | `chronosforave@gmail.com` | `demo1234` |
> | Professor | `luis.cerejeira@forave.pt` | `demo1234` |
> | Alunos | `sofia.marques@forave.pt` · `tiago.fernandes@forave.pt` · `ines.rocha@forave.pt` | `demo1234` |
> | Aluno de teste (email real) | `alunoforavecetdados@gmail.com` | `demo1234` |
>
> **Estas contas e a password `demo1234` são criadas pelo `python seed_demo.py`**
> e servem a demonstração **local** (terminal, web local e `.exe`). O **aluno de
> teste** tem um email real: é nele que se recebem os avisos automáticos por email.
>
> No **site alojado** (secção 6), o acesso de coordenador é feito com as
> credenciais que acompanham a entrega (indicadas à parte, nunca no código).

---

**Índice**

[TOC]

---

## 0. Preparação

1. Abrir a pasta do projeto no editor de código (VS Code).
2. Instalar as dependências (se necessário):
   ```
   pip install -r requirements.txt
   ```
3. Carregar os dados de demonstração (módulos, professores, alunos, avaliações,
   notas e contas de acesso):
   ```
   python seed_demo.py
   ```

    !!! resultado "Resultado esperado"
        Mensagem de conclusão com o número de módulos, alunos e contas criados.

    !!! bastidores "Nos bastidores"
        O `seed_demo.py` é **idempotente**: só cria dados de exemplo e pode correr
        as vezes que se quiser sem duplicar nem apagar nada. Isto torna a demo
        repetível — se algo correr mal a meio, basta voltar a semear.

A aplicação pode ser demonstrada em três ambientes:

| Ambiente | Comando de arranque | Endereço |
|---|---|---|
| Web (local) | `python app.py` | <http://127.0.0.1:5000> |
| Terminal | `python main.py` | — |
| Site alojado | (já em execução) | URL do alojamento (ver secção 6) |

!!! porque "Porquê"
    O mesmo domínio (as classes em `classes/` e o `gestor_cronograma.py`) serve os
    três ambientes — só muda a "casca" que o apresenta. É a prova prática da
    separação entre **lógica** e **apresentação**: a regra de negócio escreve-se
    uma vez e reutiliza-se no terminal, na web e no executável.

---

## 1. Página pública (sem sessão iniciada)

1. Abrir <http://127.0.0.1:5000> sem iniciar sessão.

    !!! resultado "Resultado esperado"
        Página inicial com a identidade do curso (CET, UFCD 10794, professor e
        grupo de trabalho).

2. Localizar a secção **"Adicionar o cronograma ao calendário"**.

    !!! resultado "Resultado esperado"
        Botão de download `.ics` e um código QR do cronograma.

    !!! rgpd "RGPD"
        O horário é assumido como informação **pública** — não são dados pessoais —
        por isso o `.ics` do curso está aberto. Os dados pessoais (as notas) **nunca**
        aparecem nesta página; ficam sempre atrás de autenticação. Separámos de
        propósito o que é público do que é privado.

3. Introduzir um endereço inexistente (ex.: `/xyz`).

    !!! resultado "Resultado esperado"
        Página de erro **404** com a identidade visual do sistema.

    !!! bastidores "Nos bastidores"
        Até as páginas de erro (403/404/500) têm a marca e são tratadas pela
        aplicação. Somam-se a cabeçalhos de segurança HTTP aplicados a todas as
        respostas — pequenos toques de "produto", não só de "trabalho de escola".

---

## 2. Perfil: Coordenador

1. Iniciar sessão com `chronosforave@gmail.com` / `demo1234`.

    !!! resultado "Resultado esperado"
        Acesso à área de Administração, com visão de todos os módulos.

    !!! porque "Porquê"
        O perfil (coordenador / professor / aluno) é determinado pelo **email** com
        que se inicia sessão, não por um campo à parte que se possa contradizer. Uma
        única fonte de verdade para a identidade evita incoerências.

### 2.1 Visão geral

1. Consultar o painel principal.

    !!! resultado "Resultado esperado"
        Cartões de resumo, um **gráfico de progresso dos módulos** (% concluído,
        ordenado dos mais atrasados para os mais adiantados), lista de módulos e
        secção de indicadores.

    !!! bastidores "Nos bastidores"
        Os indicadores e o gráfico são **calculados** a partir dos dados reais no
        momento — não são imagens fixas. O gráfico responde a uma pergunta útil ao
        coordenador ("quais os módulos atrasados?"), em vez de uma contagem sem sinal.

### 2.2 Módulos (criar, importar, editar, remover)

1. Em **Adicionar módulo**, preencher o nome, a UFCD, o professor, as **horas
   totais previstas** e o estado, e submeter.

    !!! resultado "Resultado esperado"
        O módulo passa a constar na lista de módulos.

    !!! porque "Porquê"
        Não se pede aqui "horas dadas": um módulo novo ainda não teve aulas, logo
        começa a **0**. As horas dadas passam a ser **calculadas** à medida que as
        aulas são marcadas (ver 2.5) — não é um número escrito à mão que possa
        divergir da realidade.

2. Em **Importar módulos por CSV**, selecionar `demo_modulos.csv` e importar.

    !!! resultado "Resultado esperado"
        Mensagem "Importação: N importado(s)". Módulos já existentes são assinalados
        como não importados.

    !!! bastidores "Nos bastidores"
        A importação **deteta duplicados** pela chave do módulo (o nome): reimportar
        o mesmo ficheiro não cria repetidos, apenas assinala os que saltou. Oferecer
        as duas formas — manual **e** CSV — cobre tanto a edição pontual como a
        carga rápida de um curso inteiro exportado do Excel.

3. **Editar** um módulo (professor, UFCD, estado, horas **totais**).

    !!! resultado "Resultado esperado"
        Os valores atualizados refletem-se na lista.

    !!! porque "Porquê"
        As horas **dadas** não se editam aqui — o campo é só de leitura, porque são
        calculadas a partir das aulas marcadas no cronograma (ver 2.5). Manter uma
        só forma de as alterar evita dois números a competir pela verdade.

4. Abrir um módulo e utilizar **Remover módulo** (confirmar no diálogo).

    !!! resultado "Resultado esperado"
        O módulo, com as suas avaliações e notas, é eliminado.

    !!! rgpd "RGPD"
        A remoção é **em cascata**: apagar o módulo leva as avaliações e notas
        associadas, sem deixar dados órfãos. A confirmação existe de propósito —
        é uma ação destrutiva e irreversível.

### 2.3 Professores (duas formas)

1. Em **Professores → Adicionar**, indicar nome, email e módulos que gere.

    !!! resultado "Resultado esperado"
        O professor passa a constar na lista.

    !!! porque "Porquê"
        Associar um email a um professor é o que lhe **atribui o perfil** de
        Professor ao iniciar sessão (ver secção 3). O email é a ligação entre a
        pessoa e aquilo que está autorizada a ver.

2. Em **importar professores por CSV**, selecionar `demo_professores.csv`.

    !!! resultado "Resultado esperado"
        Professores importados; mensagem de resultado.

3. Editar ou remover um professor.

    !!! resultado "Resultado esperado"
        A alteração reflete-se na lista.

### 2.4 Alunos (inscrever, importar, editar, remover)

1. Em **Formandos → Inscrever**, indicar nome, email e módulos.

    !!! resultado "Resultado esperado"
        O aluno passa a constar na lista.

2. Em **importar formandos por CSV**, selecionar `demo_formandos.csv`.

    !!! resultado "Resultado esperado"
        Alunos importados; mensagem de resultado.

3. Abrir um aluno e **editar** o nome ou os módulos inscritos; guardar.

    !!! resultado "Resultado esperado"
        Os dados atualizam-se.

    !!! porque "Porquê"
        O **email** é a identidade do aluno — é a chave a que as notas estão
        associadas — por isso não se edita. Para o mudar, remove-se e volta-se a
        inscrever. Alterar uma chave em uso é sempre uma operação delicada;
        preferimos torná-la explícita.

4. Remover um aluno.

    !!! resultado "Resultado esperado"
        Surge um pedido de confirmação; ao confirmar, o aluno e as suas notas são
        eliminados.

    !!! rgpd "RGPD"
        Apagar o aluno leva **também** as suas notas — o *direito ao apagamento* não
        fica meio feito. A confirmação prévia protege contra remoções acidentais.

### 2.5 Cronograma — agendar as aulas (data, horas e "aula dada")

1. Abrir um módulo e, na secção **Cronograma (aulas)**, indicar o **número de
   aulas** e gerar os campos. Cada aula tem três campos: a **data** (escolhida num
   calendário), as **horas** dessa aula e uma marca **"dada"** (✓). Guardar.

    !!! resultado "Resultado esperado"
        Os dias de aula ficam agendados. As **horas dadas** do módulo passam a ser a
        **soma das horas das aulas marcadas como dadas** — o indicador "X/Y h" e as
        "horas em falta" atualizam-se sozinhos.

    !!! porque "Porquê"
        As horas dadas são **calculadas**, não escritas à mão. Uma só fonte de
        verdade (as aulas marcadas) alimenta o indicador de progresso e as horas em
        falta — nunca há um total manual a contradizer o cronograma.

    !!! bastidores "Nos bastidores"
        Cada aula (data + horas + "dada") é guardada numa coluna **"Sessoes"** (em
        JSON) na Google Sheet, de forma **retrocompatível**: módulos antigos, que só
        tinham datas e um total escrito à mão, continuam a funcionar. Guardar o
        cronograma **não apaga** um total já importado enquanto não se marcar
        nenhuma aula — os módulos vindos de CSV estão protegidos.

2. Marcar mais uma aula como **dada** (✓) e guardar de novo.

    !!! resultado "Resultado esperado"
        As horas dadas aumentam e as horas em falta diminuem, sem qualquer edição
        manual do número.

    !!! porque "Módulos importados por CSV"
        O CSV traz as horas **totais** e as datas das aulas, mas **não** as horas de
        cada aula nem a marca "dada" — é aqui, no cronograma, que essas se definem à
        medida que o curso avança. (Decisão consciente: pôr horas por sessão no CSV
        seria uma segunda porta de entrada para o mesmo dado, a arriscar
        divergências.)

### 2.6 Exportação e auditoria

1. Gerar o **Relatório PDF**.

    !!! resultado "Resultado esperado"
        Download de um PDF com módulos e avaliações (com indicador de progresso
        durante a geração).

2. Utilizar a exportação **.ics** (curso completo) e, num módulo, **.ics + QR**.

    !!! resultado "Resultado esperado"
        Ficheiro de calendário / código QR do módulo.

    !!! porque "Porquê"
        O QR só é usado onde acrescenta algo: como ponte de um meio **não clicável**
        (um cartaz, um slide) para o telemóvel. Na própria página não se põe um QR
        para a própria página — seria redundante.

3. Consultar o **Registo de alterações** e **Descarregar o registo completo (CSV)**.

    !!! resultado "Resultado esperado"
        Histórico das operações (autor, ação, data) — no ecrã as mais recentes, e o
        **CSV com o histórico completo** para arquivo/auditoria externa. Nas notas, é
        apresentado o valor anterior e o novo.

    !!! rgpd "Accountability"
        O registo de auditoria responde a "quem fez o quê e quando". Guardar o valor
        **anterior → novo** nas notas dá rastreabilidade real — importante porque a
        autorização é por perfil, e o registo é a rede de segurança que a acompanha.

---

## 3. Perfil: Professor

Terminar sessão e iniciar com `luis.cerejeira@forave.pt` / `demo1234`.

1. Aceder à Área do Professor ("Os meus módulos"). No topo, um **Calendário**
   com as aulas e avaliações **dos seus módulos** (mesma peça da área do aluno,
   agora filtrada ao âmbito do professor), com o botão **.ics** e o **QR** para
   levar o cronograma para o telemóvel.

    !!! resultado "Resultado esperado"
        É apresentado **apenas** o módulo atribuído (*Programação Avançada com
        Python*); os restantes módulos não são visíveis. O calendário mostra só os
        eventos desse módulo.

    !!! porque "Porquê"
        A autorização é **por âmbito**: o professor vê e gere só os seus módulos, não
        é tudo-ou-nada. Foi uma evolução deliberada de um controlo de acesso simples
        (só coordenador podia tudo) para permissões mais finas por módulo.

    !!! rgpd "Accountability"
        Tudo o que o professor altera (notas, cronograma, avaliações) fica no
        **registo de auditoria** com o **email dele** como autor. O professor é
        autónomo no seu módulo, mas nada do que faz fica sem rasto — o coordenador
        vê o histórico completo (o professor não vê a auditoria global).

2. Confirmar a ausência das secções de coordenação (criar módulos, gerir
   professores e formandos, auditoria global).

    !!! resultado "Resultado esperado"
        Estas secções não estão disponíveis para o professor.

3. No **Cronograma (aulas)** do módulo, marcar como **dada** (✓) uma aula ainda por
   dar e guardar.

    !!! resultado "Resultado esperado"
        As **horas dadas** do módulo aumentam (soma das aulas dadas) e as horas em
        falta diminuem.

    !!! porque "Porquê"
        O professor gere as horas do seu módulo **sem depender do coordenador** — a
        autorização por âmbito torna-o autónomo dentro do que é seu.

4. Criar ou editar uma **avaliação** no módulo. A **data** escolhe-se num
   calendário; cada campo tem uma dica do que se espera (só a *Descrição* é
   obrigatória). Opcionalmente, marcar **"Avisar a turma por email"**.

    !!! resultado "Resultado esperado"
        A avaliação passa a constar; o campo "tipo" apresenta sugestões (Teste,
        Projeto, etc.). Com a caixa marcada e uma data definida, cada aluno inscrito
        recebe um email a anunciar (ou atualizar) a avaliação.

    !!! bastidores "Nos bastidores"
        As sugestões vêm de uma lista (`datalist`) para uniformizar os tipos sem
        obrigar a menus rígidos. O aviso à turma reutiliza o mesmo mecanismo do
        reagendamento de aulas (envio individual a cada aluno, nunca em conjunto).

5. Lançar uma **nota** a um aluno. Para demonstrar a **notificação individual**,
   marcar a opção **"avisar cada aluno da sua nota por email"** antes de guardar —
   utilizar o aluno de teste `alunoforavecetdados@gmail.com` para verificar a
   receção (secção 5).

    !!! resultado "Resultado esperado"
        A nota é registada; com a opção marcada, é enviado ao aluno um email com a
        sua nota. A nota fica visível na área do aluno (secção 4).

    !!! rgpd "RGPD"
        O aviso de nota é **individual**: cada aluno é notificado apenas da **sua**
        nota, nunca das dos outros. A notificação respeita o mesmo isolamento de
        dados que o resto do sistema.

6. Reagendar uma aula (alterar uma data) com a opção **"avisar a turma"** e um
   motivo.

    !!! resultado "Resultado esperado"
        A data é atualizada e é preparada a notificação à turma (ver secção 5).

    !!! porque "Porquê"
        Este era o problema real que deu origem ao projeto: as mudanças de data não
        chegavam a tempo aos formandos. Aqui, reagendar e avisar a turma é **uma só
        ação** — a comunicação deixa de depender de alguém se lembrar de a fazer.

---

## 4. Perfil: Aluno

Terminar sessão e iniciar com `sofia.marques@forave.pt` / `demo1234`. O aluno entra
na sua página pessoal, **"A minha área"** (calendário + notas).

1. Consultar **"O meu calendário"** no topo da página. Alternar entre **Mês** e
   **Semana** e navegar com **‹ ›** e **Hoje**.

    !!! resultado "Resultado esperado"
        Um calendário com as **aulas** (verde; as já dadas a verde-suave com ✓) e as
        **avaliações** (dourado) dos módulos do aluno. O dia de hoje fica destacado.

    !!! bastidores "Nos bastidores"
        O calendário é **feito de raiz** (`static/calendario.js`), sem bibliotecas
        externas — só JavaScript e o DOM. O servidor prepara os eventos **só deste
        aluno** (RGPD); o cliente desenha as vistas mês/semana.

2. Por baixo do calendário, usar **"Adicionar ao meu telemóvel (.ics)"** ou o
   **QR code**.

    !!! resultado "Resultado esperado"
        Descarrega um ficheiro `.ics` (ou, pelo QR, abre-o no telemóvel) que junta as
        aulas ao calendário do dispositivo.

    !!! porque "Porquê"
        O QR é a ponte ecrã→telemóvel: reutiliza o `.ics` **público** do curso (o
        horário não são dados pessoais — as notas nunca saem por aqui).

2. Consultar **As minhas notas**.

    !!! resultado "Resultado esperado"
        Módulos em que está inscrita, cada avaliação com a nota respetiva e a **nota
        final (UFCD)** calculada por média ponderada (ex.: **16.9** em Programação
        Avançada).

    !!! bastidores "Nos bastidores"
        A nota final é uma **média ponderada** pelos pesos das avaliações, calculada
        a partir das notas lançadas — o aluno vê o resultado sem ter de fazer contas.

2. Verificar a nota lançada pelo professor na secção 3.

    !!! resultado "Resultado esperado"
        A nota está visível para a aluna.

3. Confirmar o isolamento de dados.

    !!! resultado "Resultado esperado"
        A aluna não tem acesso a notas de outros alunos.

    !!! rgpd "RGPD"
        O isolamento de dados é um requisito, não um detalhe: cada aluno vê apenas o
        que é seu. É a mesma regra que atravessa a página pública, as notificações e
        a área pessoal.

5. (Opcional) Iniciar sessão como `tiago.fernandes@forave.pt`.

    !!! resultado "Resultado esperado"
        Apenas os dados desse aluno são apresentados.

---

## 5. Notificações por email

O sistema envia avisos por email em três casos: **nota individual** ao aluno,
**reagendamento** de uma aula à turma e **avaliação marcada/atualizada** à turma.

1. Lançar uma nota (ou reagendar uma aula) que envolva o aluno de teste
   `alunoforavecetdados@gmail.com`.
2. Verificar a caixa de correio desse aluno, **incluindo a pasta de Spam**.

    !!! resultado "Resultado esperado"
        Receção do aviso correspondente. O email vem de **"Cronograma FORAVE"**
        (`chronosforave@gmail.com`), mas ao clicar em **Responder** a resposta abre
        para **quem fez a alteração** (ex.: o professor).

!!! porque "Remetente institucional, resposta pessoal (Reply-To)"
    O remetente é **sempre** o endereço institucional verificado na Brevo — não pode
    ser o email pessoal do professor (a Brevo rejeitaria um remetente não verificado).
    Para não perder o toque pessoal, define-se um **Reply-To** com o email de quem
    despoletou o aviso: o envio continua institucional (e aceite), mas as **respostas
    dos alunos vão ter com o professor/coordenador** que agiu.

!!! bastidores "Nos bastidores — porquê a Brevo"
    No alojamento (Render), o envio direto por SMTP está **bloqueado** — uma
    restrição comum nos serviços de alojamento para travar spam. Por isso o envio em
    produção passa por um **serviço transacional (Brevo)**, por API. Localmente, o
    envio direto por SMTP continua disponível como alternativa. A arquitetura prevê
    os dois caminhos.

!!! rgpd "Porquê pode ir para Spam"
    O remetente da demo é um endereço **gratuito** (Gmail). Pelas regras de
    autenticação de email (SPF/DKIM/DMARC), uma mensagem enviada em nome de um
    endereço gratuito através de um serviço transacional pode ser classificada como
    **spam** — daí a instrução de verificar essa pasta. Em produção recomenda-se um
    **domínio próprio**. É uma limitação conhecida e assumida, não um defeito por
    resolver.

> **Acesso à caixa de teste:** por segurança, as credenciais de acesso à conta
> `alunoforavecetdados@gmail.com` não constam do projeto; são indicadas na
> mensagem de entrega.

---

## 6. Outras interfaces e canais

1. **Terminal:** executar `python main.py`.

    !!! resultado "Resultado esperado"
        Menu por opções, sobre os mesmos dados da versão web.

2. **Executável (.exe):** descarregar o **`GestorCronograma-v1.0.zip`** da **Release
   v1.0** (na página do GitHub → "Releases"), extrair a pasta, e **duplo-clique** em
   `GestorCronograma.exe`. *(Para quem quiser reconstruir a partir do código, ver
   `INSTRUCOES_EXE.md`.)*

    !!! resultado "Resultado esperado"
        A aplicação de terminal abre **já com a demo carregada** (módulos,
        professores e alunos), **sem precisar de Python instalado** — corre offline.

    !!! bastidores "Nos bastidores"
        O `.exe` é gerado com **PyInstaller** (`build_exe.ps1` + `cronograma.spec`):
        empacota o programa de terminal (`main.py`) e as bibliotecas numa pasta; os
        dados de demonstração vão ao lado, em `dados/`.

3. **Site alojado:** abrir o URL do alojamento e iniciar sessão como coordenador;
   importar `demo_modulos.csv`, `demo_formandos.csv` e `demo_professores.csv`.

    !!! resultado "Resultado esperado"
        Os dados ficam disponíveis no site (leitura a partir do Google Sheet).

4. **Instalação como aplicação (PWA):** a partir do site, instalar no dispositivo.

    !!! resultado "Resultado esperado"
        O sistema fica acessível como aplicação.

!!! porque "Porquê tantos canais"
    Terminal, web, executável, PDF, QR, `.ics` e email são todos "cascas" sobre a
    **mesma lógica**. Mostrá-los prova que a arquitetura separa a regra de negócio
    da forma como é consumida — o objetivo desde o início.

---

## 7. Reposição de password

1. No ecrã de início de sessão, selecionar **Esqueci-me da password** e indicar um
   email.

    !!! resultado "Resultado esperado"
        É gerado um link seguro (token assinado, de uso único e com validade) para
        definir uma nova password.

    !!! rgpd "Nos bastidores — segurança"
        As passwords são guardadas como **hash** (num só sentido) — nem nós as vemos.
        Por isso "esqueci-me" resolve-se com uma **reposição**, não com uma
        recuperação: gera-se um link assinado e temporário, em vez de reenviar a
        password antiga.

---

## 8. Estrutura do código (para consulta)

Cada ficheiro inclui um cabeçalho com o seu propósito; cada classe e método têm
documentação (docstrings). Percurso recomendado:

- `README.md` e `ESTRUTURA_PROJECTO.md` — arquitetura, mapa de ficheiros e decisões.
- `classes/` — domínio (POO): `modulo.py`, `formando.py`, `avaliacao_final.py`,
  `professor.py`, `gerador_ics.py`, `token_modulo.py`, `autenticacao.py`, entre outros.
- `gestor_cronograma.py` — orquestração do domínio (CRUD e persistência).
- `app.py` (web) e `main.py` (terminal) — interfaces sobre o mesmo domínio.
- `testes/` — testes automáticos:
  ```
  python -m unittest discover -s testes
  ```

---

## 9. Alinhamento com a matéria de Python Avançado

O projeto aplica, num problema real, os conceitos trabalhados ao longo da UFCD —
partindo de Python puro (terminal + POO) e crescendo para web + cloud, sempre com
a **mesma lógica** no centro.

| Conceito da UFCD | Onde se aplica no projeto |
|---|---|
| **Programação Orientada a Objetos** (classes, atributos, métodos) | Pasta `classes/`: `Modulo`, `Formando`, `Professor`, `Avaliacao`, `GestorCronograma`, `Utilizador`… |
| **Responsabilidade única / separação de camadas** | A lógica **devolve dados** (sem `print`); a apresentação fica para quem chama (`main.py` no terminal, `app.py` na web) |
| **Dicionários e listas** | Estrutura dos dados em memória; `to_dict()` / `from_dict()` para converter objeto ↔ dicionário |
| **Ficheiros e persistência (JSON)** | `dados/*.json` como fonte de verdade local (stdlib `json`) |
| **Tratamento de erros (`try`/`except`)** | Importação de CSV robusta (conta erros por linha), rede/email com *timeout* — nunca "rebenta" |
| **Funções com parâmetros e retorno** | Todos os métodos do domínio; funções puras e testáveis |
| **Strings e f-strings** | Mensagens, corpos de email, relatório PDF |
| **Ciclos e condições** | Percursos de dados (`for`/`if`) em todo o domínio |
| **Modularização (multi-ficheiro)** | Domínio (`classes/`) separado das interfaces (`app.py` / `main.py`) e das integrações |
| **Integração com serviços/APIs** | Google Sheets (`gspread`), email transacional (Brevo por HTTP), web (Flask) |
| **Boas práticas de desenvolvimento** | Git/GitHub, `.gitignore`, `requirements.txt`, **testes automáticos** (unittest) e **CI** |

> Cada ficheiro tem um cabeçalho a explicar o seu propósito e a ligação à matéria;
> cada classe e método têm *docstrings*. É o percurso recomendado para o professor
> confirmar, no código, que cada decisão segue o que foi dado nas aulas.

---

## Resumo das funcionalidades

- Três perfis (Coordenador, Professor, Aluno) com isolamento de dados (RGPD).
- Controlo de horas por aula: cada sessão tem horas e marca de "dada"; as horas
  dadas (e as horas em falta) são calculadas automaticamente.
- Múltiplos canais sobre a mesma lógica: terminal, web, PDF, QR e `.ics` / email.
- Duas formas de carregamento em massa: manual e CSV (módulos, formandos, professores).
- Execução local (terminal, web, executável) e alojada (site, PWA, Google Sheet).
- Registo de alterações (auditoria), notificações, cabeçalhos de segurança e
  acessibilidade.
