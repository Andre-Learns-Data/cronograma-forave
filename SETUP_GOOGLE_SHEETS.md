> ⚠️ **Documento histórico (Maio/2026) — ainda útil como guia de setup.** Os passos de
> criar a Service Account, fazer download do `credentials.json` e partilhar a spreadsheet
> **continuam válidos**. Nota: o caminho do `credentials.json` pode diferir (este guia
> usa `classes/`; o projeto lê o caminho do `.env`), e para o **alojamento** ver
> `DEPLOY.md`. **Estado atual do sistema:** `README.md` e `ESTRUTURA_PROJECTO.md`.
> Mantém-se intacto para preservar o histórico.

---

# 🔧 Guia de Configuração — Google Sheets

Este guia explica como configurar a integração com Google Sheets para o Dashboard.

---

## 📋 Pré-requisitos

- Conta Google
- Acesso ao Google Cloud Console
- Spreadsheet criada no Google Drive (com abas: Módulos, Professores, Formandos, Alterações)

---

## ✅ Passo 1: Criar Service Account no Google Cloud

### 1.1 Aceder ao Google Cloud Console

1. Ir para https://console.cloud.google.com
2. Criar um novo projeto (ou usar um existente)

### 1.2 Activar Google Sheets API

1. Na barra de pesquisa, procurar `Google Sheets API`
2. Clicar em "Google Sheets API"
3. Clicar no botão **ACTIVATE** (ou "Enable")

### 1.3 Criar Service Account

1. Ir para **"Credenciais"** (Credentials)
2. Clicar em **"Criar Credenciais"** → **"Service Account"**
3. Preencher o formulário:
   - Nome: `cronograma-dashboard` (ou similar)
   - ID: auto-preenchido
   - Descrição: `Service account para dashboard de cronograma`
4. Clicar **"Criar e Continuar"**

### 1.4 Fazer Download das Credenciais

1. Na página da Service Account, ir para aba **"Chaves"** (Keys)
2. Clicar em **"Adicionar Chave"** → **"Criar nova chave"**
3. Escolher formato **JSON**
4. Clicar **"Criar"** — o ficheiro `credentials.json` será descarregado automaticamente

---

## 💾 Passo 2: Instalar credentials.json no Projeto

1. Na pasta do projeto, abrir a pasta `classes/`
2. Colar o ficheiro `credentials.json` aqui:
   ```
   <pasta-do-projeto>\classes\credentials.json
   ```

⚠️ **IMPORTANTE**: O ficheiro contém dados sensíveis — **NUNCA comita para Git**!

---

## 🔗 Passo 3: Partilhar Spreadsheet com Service Account

### 3.1 Obter Email do Service Account

1. Voltar ao Google Cloud Console
2. Ir para **"Service Accounts"**
3. Procurar a Service Account criada
4. Copiar o email: `cronograma-dashboard@seu-projeto.iam.gserviceaccount.com`

### 3.2 Partilhar Spreadsheet

1. Abrir a spreadsheet no Google Drive
2. Clicar no botão **"Partilhar"** (Share) — canto superior direito
3. Colar o email do Service Account
4. Conceder permissão de **"Editor"**
5. Clicar **"Partilhar"**

---

## 📊 Passo 4: Obter ID ou Nome da Spreadsheet

### Opção A: Usar o Nome (mais fácil)

Se a spreadsheet se chama `cronograma` (ou similar):

1. Abrir `app.py`
2. Procurar a linha:
   ```python
   google_sheets = GoogleSheetsSync(credenciais_path="classes/credentials.json", spreadsheet_id_ou_nome="cronograma")
   ```
3. Deixar como está (se o nome da spreadsheet for `cronograma`)
4. Ou alterar para o nome correto

### Opção B: Usar o ID (mais preciso)

1. Abrir a spreadsheet no Google Drive
2. Copiar o ID da URL:
   ```
   https://docs.google.com/spreadsheets/d/[ESTE_É_O_ID]/edit
   ```
3. Abrir `app.py`
4. Alterar a linha:
   ```python
   spreadsheet_id_ou_nome="1A2B3C4D5E6F7G8H9I0J"  # Cole o ID aqui
   ```

---

## 🧪 Passo 5: Testar a Conexão

Executar o script de teste:

```bash
python test_google_sheets_connection.py
```

Este script vai:

✅ Verificar se `credentials.json` existe  
✅ Tentar conectar ao Google Sheets  
✅ Ler dados da spreadsheet  
✅ Validar permissões  

**Esperado**: Todos os testes passarem com ✅

---

## 🚀 Passo 6: Iniciar o Dashboard

```bash
python app.py
```

Se tudo estiver correto:

```
[STARTUP] Inicializando conexão com Google Sheets...
✅ Google Sheets: ligação estabelecida com 'cronograma'
[SUCCESS] Dashboard conectado ao Google Sheets!

[INFO] Encontrados X registos no cronograma
```

Depois abrir: http://127.0.0.1:5000

---

## 🐛 Troubleshooting

### ❌ "credentials.json não encontrado"

**Solução**: Verificar se o ficheiro está em `classes/credentials.json`

### ❌ "Spreadsheet não encontrada"

**Solução**:
- Verificar se o nome/ID está correto em `app.py`
- Verificar se partilhou a spreadsheet com o Service Account
- Usar `spreadsheet_id_ou_nome=ID_DA_SPREADSHEET` (versão ID é mais fiável)

### ❌ "Erro de permissão (403)"

**Solução**:
- Ir ao Google Cloud Console
- Verificar se a Service Account tem permissão na API
- Partilhar a spreadsheet com o email do Service Account (`Partilhar` → adicionar email)

### ❌ "Nenhum dado encontrado"

**Solução**:
- Verificar se a spreadsheet tem abas: "Módulos", "Professores", "Formandos", "Alterações"
- Preenchê-las com dados
- O script `test_google_sheets_connection.py` mostra as abas disponíveis

---

## 📝 Estrutura da Spreadsheet

A spreadsheet deve ter estas abas:

### Aba 1: "Módulos"

| Nome | Professor | Horas Totais | Horas Dadas | Horas Restantes | Progresso (%) | Estado | Datas |
|------|-----------|--------------|-------------|-----------------|---------------|--------|-------|
| Matemática | Prof. Lui | 50 | 20 | 30 | 40 | Ativo | 01/06, 02/06, 03/06 |
| Física | Prof. Renato | 40 | 10 | 30 | 25 | Ativo | 02/06, 03/06 |

### Aba 2: "Professores"

| Nome | Email | Telefone | Módulos |
|------|-------|----------|---------|
| Prof. Lui | lui@example.com | 123456789 | Matemática, Química |
| Prof. Renato | renato@example.com | 987654321 | Física |

### Aba 3: "Formandos"

| Nome | Email | Módulos Inscritos |
|------|-------|-------------------|
| João | joao@example.com | Matemática, Física |
| Maria | maria@example.com | Química |

### Aba 4: "Alterações"

| Data Registo | Módulo | Data Original | Data Nova | Motivo | Autor |
|--------------|--------|---------------|-----------|--------|-------|
| 28/05/2026 | Matemática | 01/06 | 02/06 | Sala indisponível | Admin |

---

## ✅ Tudo Pronto!

Se conseguiu executar sem erros, o dashboard agora busca dados reais do Google Sheets!

**Próximas funcionalidades**:
- Dashboard mostrará dados do Google Sheets
- Sincronização automática quando mudar dados
- Exportação de PDF do cronograma
- Notificações por email

---

**Dúvidas?** Consulte:
- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
