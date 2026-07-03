# Como criar o `.exe` (programa de terminal)

Isto transforma o Gestor de Cronograma (versão de **terminal**, `main.py`)
num **executável Windows** — um ficheiro que se abre com duplo-clique,
sem ser preciso ter o Python instalado. Serve para dar o programa a
alguém (ou levá-lo numa pen) e correr em qualquer PC com Windows.

> Nota: o `.exe` é a versão de **terminal** (menus por números). A versão
> web/dashboard é outra coisa e vive no site alojado (Render).

---

## Passo a passo (fácil)

1. Abre o **PowerShell** na pasta do projecto.
   - No Explorador de Ficheiros, entra na pasta do projecto, escreve
     `powershell` na barra de endereço e carrega Enter.

2. Escreve este comando e carrega Enter:

   ```powershell
   .\build_exe.ps1
   ```

   - Se aparecer um erro a dizer que "a execução de scripts está
     desativada", corre primeiro isto e tenta de novo:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     ```

3. Espera 1–2 minutos. No fim aparece a mensagem **OK!** com o caminho:

   ```
   dist\GestorCronograma\GestorCronograma.exe
   ```

4. Abre a pasta `dist\GestorCronograma` e faz **duplo-clique** em
   `GestorCronograma.exe`. O programa arranca numa janela de terminal.

Pronto. 🎉

---

## Como partilhar / usar noutro PC

- **Copia a pasta `GestorCronograma` inteira** (não só o `.exe` — ele
  precisa dos ficheiros que estão ao lado dele).
- Corre o `.exe` **de dentro dessa pasta**.
- Na primeira vez, o programa cria sozinho uma pasta **`dados/`** ao lado
  do `.exe` — é aí que ele guarda os módulos, notas, etc. Fica tudo local
  nesse PC.

## (Opcional) Google Sheets e email no `.exe`

O programa funciona **sem** isto — são bónus. Para os activar no `.exe`,
põe ao lado do executável (dentro da pasta `GestorCronograma`):

- um ficheiro **`.env`** com as configurações (o mesmo formato do projecto);
- o **`credentials.json`** do Google, se usares o Google Sheets.

Sem estes ficheiros, o menu mostra `[Google Sheets: OFF]` / `[Email: OFF]`
e o resto do programa continua a funcionar normalmente.

---

## Detalhes técnicos (para o relatório)

- Ferramenta: **PyInstaller** (modo *onedir* — uma pasta com o `.exe` e as
  bibliotecas). Escolheu-se *onedir* em vez de *onefile* porque o programa
  **grava dados** na pasta `dados/`: no modo *onefile* o conteúdo é extraído
  para uma pasta temporária que desaparece no fim, e as gravações perder-se-iam.
- A configuração está em [`cronograma.spec`](cronograma.spec); o build é
  automatizado por [`build_exe.ps1`](build_exe.ps1).
- O PyInstaller é uma ferramenta de **construção**, não uma dependência do
  programa — por isso não está no `requirements.txt`; o script instala-o
  quando é preciso.
- Antivírus: executáveis feitos com PyInstaller às vezes são assinalados por
  engano (falso positivo). É normal com programas não assinados digitalmente.
