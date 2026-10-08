# Guia de demonstração — Gestor de Cronograma FORAVE

Este guia serve para **mostrar todas as funcionalidades** na defesa, de forma
ordenada, e traz os **ficheiros de exemplo** necessários para as importações.

> **Dica:** segue o roteiro de cima para baixo. Cada passo mostra uma
> funcionalidade diferente, sem repetir trabalho.

---

## 1. Acessos (todas as contas usam a password `demo1234`)

| Papel | Email | O que vê |
|---|---|---|
| **Coordenador** | `chronosforave@gmail.com` | Gere tudo (módulos, professores, formandos, notas, registo) |
| **Professor** | `luis.cerejeira@forave.pt` | Só o módulo que lhe está atribuído |
| **Aluno** | `sofia.marques@forave.pt` | Só as suas notas |
| **Aluno (email real)** | `alunoforavecetdados@gmail.com` | Recebe os emails automáticos |

---

## 2. Ficheiros de exemplo (nesta pasta)

| Ficheiro | Serve para | Formato (cabeçalho) |
|---|---|---|
| `importar_modulos_exemplo.csv` | Importar módulos em massa | `ufcd,nome,professor,horas_totais,horas_dadas,estado,datas` |
| `importar_professores_exemplo.csv` | Importar professores | `nome,email,telefone,modulos` |
| `importar_formandos_exemplo.csv` | Importar formandos (alunos) | `nome,email,modulos` |

Regras dos CSV:
- **Datas** (módulos) e **módulos** (professores/formandos) separam-se por `;`
  (ex.: `20/10/2026;27/10/2026` ou `Python;SQL`).
- **Duplicados são saltados**: o nome é a chave dos módulos, o email é a chave
  de professores e formandos. Reimportar o mesmo ficheiro não cria repetidos.
- Os exemplos foram feitos para **não colidir** com os dados já semeados —
  por isso importam mesmo (não aparecem como "saltados").

> **Ordem recomendada na importação:** primeiro **módulos**, depois
> **professores**, e por fim **formandos** (que já se inscrevem nos módulos
> novos).

---

## 3. Roteiro de demonstração (passo a passo)

### A. Entrar como Coordenador
1. Abrir a demo e iniciar sessão com `chronosforave@gmail.com` / `demo1234`.
2. **Visão geral (dashboard):**
   - KPIs (módulos, conclusão média, formandos, professores).
   - **Próximas aulas e avaliações** (o que vem aí).
   - **Precisa de atenção** (módulos sem avaliações, etc.).
   - **Progresso por módulo** e **Estado dos módulos** (gráficos).
   - **Calendário** com as aulas e avaliações + botão **.ics** e **QR**.
3. **Pesquisa rápida** (barra de topo): escrever, por exemplo, `bases` e ver a
   lista a filtrar em tempo real.

### B. Gerir Módulos
4. Menu **Módulos → Adicionar módulo**: criar um módulo à mão (ex.: nome, UFCD,
   professor, horas, estado).
5. Abrir um módulo e **editar o cronograma**: indicar o nº de aulas, escolher
   as datas no calendário, marcar as aulas já dadas.
6. **Módulos → Importar CSV**: carregar `importar_modulos_exemplo.csv`.
   → aparece o resumo "N importados / M saltados".

### C. Gerir Professores
7. Menu **Professores → Adicionar / Importar**: importar
   `importar_professores_exemplo.csv`.
8. Abrir um professor e confirmar os módulos que lhe ficaram associados.

### D. Gerir Formandos (e RGPD)
9. Menu **Formandos → Inscrever / Importar**: importar
   `importar_formandos_exemplo.csv`.
10. Inscrever um formando à mão (nome + email + módulos).
11. **Direito ao apagamento (RGPD):** remover um formando e explicar que apaga
    o aluno **e as suas notas** (ação irreversível, com confirmação).

### E. Lançar notas
12. Abrir um módulo com avaliações, lançar/editar notas de um aluno e confirmar
    o cálculo da **nota final** (média ponderada pelos pesos).

### F. Registo de alterações (auditoria)
13. Menu **Registo de alterações**: mostrar que cada ação ficou registada
    (quem, o quê, quando).
14. Clicar **Descarregar registo completo (CSV)** — prova de auditoria externa.

### G. Papéis diferentes (âmbito)
15. Sair e entrar como **professor** (`luis.cerejeira@forave.pt`): vê só o
    módulo dele.
16. Sair e entrar como **aluno** (`sofia.marques@forave.pt`): vê só as suas
    notas.

### H. App no telemóvel / PWA
17. No telemóvel, mostrar o **menu em gaveta** (☰).
18. Mostrar o botão **Instalar app** (cria o ícone no ecrã) e o **aviso de
    offline** (só dá para editar com ligação à internet).

---

## 4. Repor a demo a um estado limpo

Depois de o professor mexer nos dados, podes repor tudo ao estado inicial
(com as datas já perto de agora):

1. No painel do alojamento (Render), nas variáveis de ambiente do serviço,
   pôr **`RESEED_DEMO=1`** e fazer *deploy* (ou reiniciar).
2. O arranque apaga os dados e **semeia de novo** a demonstração.
3. **Importante:** voltar a pôr **`RESEED_DEMO=0`** (ou apagar a variável) a
   seguir — senão cada reinício do servidor volta a apagar o que se fizer.

> A password de todas as contas continua a ser `demo1234`.
