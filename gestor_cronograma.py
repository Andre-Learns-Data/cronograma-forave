# ============================================================
# gestor_cronograma.py — Classe GestorCronograma
# ============================================================
# Classe orquestradora — é o cérebro do sistema.
# Coordena as outras classes (Modulo, Professor, Formando,
# Alteracao, Notificacao) e gere a persistência dos dados
# em ficheiros JSON.
#
# Responsabilidades:
#   - Carregar e guardar dados (JSON)
#   - Adicionar, listar e procurar entidades
#   - Registar alterações ao cronograma
#   - Gerar e enviar notificações
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários, listas),
#               Sessão Online 6 (ficheiros), Aula 7 (try/except)
# ============================================================

import json
import os

from classes.alteracao import Alteracao, alteracao_from_dict
from classes.avaliacao_final import Avaliacao
from classes.formando import Formando, formando_from_dict

# Importar as classes e funções from_dict de cada módulo
from classes.modulo import Modulo, modulo_from_dict
from classes.notificacao import Notificacao, notificacao_from_dict
from classes.professor import Professor, professor_from_dict


class GestorCronograma:
    """
    Classe orquestradora que coordena todo o sistema.

    Atributos:
        modulos (list): Lista de objectos Modulo.
        professores (list): Lista de objectos Professor.
        formandos (list): Lista de objectos Formando.
        alteracoes (list): Lista de objectos Alteracao.
        notificacoes (list): Lista de objectos Notificacao.
        pasta_dados (str): Caminho da pasta onde ficam os JSON.
    """

    def __init__(self, pasta_dados="dados"):
        """
        Construtor — inicializa o gestor com listas vazias.

        Parâmetros:
            pasta_dados (str): Pasta onde os ficheiros JSON são
                               guardados. Por defeito: "dados".
        """
        self.modulos = []
        self.professores = []
        self.formandos = []
        self.alteracoes = []
        self.notificacoes = []
        self.pasta_dados = pasta_dados

        # Criar a pasta de dados se não existir
        # os.path.exists() verifica se a pasta já existe
        # os.makedirs() cria a pasta (e sub-pastas se necessário)
        if not os.path.exists(self.pasta_dados):
            os.makedirs(self.pasta_dados)

    # ============================================================
    # PERSISTÊNCIA — Guardar e carregar dados em JSON
    # ============================================================

    def guardar_dados(self):
        """
        Grava todas as listas nos respectivos ficheiros JSON.

        Fluxo:
            1. Converter cada objecto em dicionário com to_dict()
            2. Juntar todos os dicionários numa lista
            3. Gravar a lista no ficheiro com json.dump()

        Conceito: É o padrão lista vazia + for + append,
        mas em vez de append(texto), é append(dicionário).
        """
        # --- Guardar módulos ---
        lista_dicts = []
        for m in self.modulos:
            lista_dicts.append(m.to_dict())

        caminho = self.pasta_dados + "/modulos.json"
        ficheiro = open(caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

        # --- Guardar professores ---
        lista_dicts = []
        for p in self.professores:
            lista_dicts.append(p.to_dict())

        caminho = self.pasta_dados + "/professores.json"
        ficheiro = open(caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

        # --- Guardar formandos ---
        lista_dicts = []
        for f in self.formandos:
            lista_dicts.append(f.to_dict())

        caminho = self.pasta_dados + "/formandos.json"
        ficheiro = open(caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

        # --- Guardar alterações ---
        lista_dicts = []
        for a in self.alteracoes:
            lista_dicts.append(a.to_dict())

        caminho = self.pasta_dados + "/alteracoes.json"
        ficheiro = open(caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

        # --- Guardar notificações ---
        lista_dicts = []
        for n in self.notificacoes:
            lista_dicts.append(n.to_dict())

        caminho = self.pasta_dados + "/notificacoes.json"
        ficheiro = open(caminho, "w", encoding="utf-8")
        json.dump(lista_dicts, ficheiro, indent=4, ensure_ascii=False)
        ficheiro.close()

    def carregar_dados(self):
        """
        Carrega todos os dados dos ficheiros JSON.

        Se um ficheiro não existir (primeira vez que o programa
        corre), a lista correspondente fica vazia — sem erro.

        Fluxo:
            1. Abrir o ficheiro JSON
            2. json.load() devolve uma lista de dicionários
            3. Converter cada dicionário num objecto com from_dict()
            4. Guardar na lista correspondente

        Conceito: try/except FileNotFoundError — padrão da Aula 7.
        """
        # --- Carregar módulos ---
        self.modulos = []
        caminho = self.pasta_dados + "/modulos.json"
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                modulo = modulo_from_dict(d)
                self.modulos.append(modulo)
        except FileNotFoundError:
            pass  # Ficheiro não existe — lista fica vazia

        # --- Carregar professores ---
        self.professores = []
        caminho = self.pasta_dados + "/professores.json"
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                professor = professor_from_dict(d)
                self.professores.append(professor)
        except FileNotFoundError:
            pass

        # --- Carregar formandos ---
        self.formandos = []
        caminho = self.pasta_dados + "/formandos.json"
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                formando = formando_from_dict(d)
                self.formandos.append(formando)
        except FileNotFoundError:
            pass

        # --- Carregar alterações ---
        self.alteracoes = []
        caminho = self.pasta_dados + "/alteracoes.json"
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                alteracao = alteracao_from_dict(d)
                self.alteracoes.append(alteracao)
        except FileNotFoundError:
            pass

        # --- Carregar notificações ---
        self.notificacoes = []
        caminho = self.pasta_dados + "/notificacoes.json"
        try:
            ficheiro = open(caminho, "r", encoding="utf-8")
            lista_dicts = json.load(ficheiro)
            ficheiro.close()

            for d in lista_dicts:
                notificacao = notificacao_from_dict(d)
                self.notificacoes.append(notificacao)
        except FileNotFoundError:
            pass

    # ============================================================
    # MÓDULOS — Adicionar, listar, procurar
    # ============================================================

    def adicionar_modulo(self, nome, professor, horas_totais, horas_dadas, estado, datas, ufcd=""):
        """
        Cria e adiciona um novo módulo à lista.

        Parâmetros:
            nome, professor, horas_totais, horas_dadas, estado, datas

        Retorna:
            Modulo: O objecto criado (útil para a camada que chama
                    decidir como apresentar o resultado).

        Evolução (Sessão 3): Tirado o print() de dentro da função.
        A regra da Sessão 2 (secção 5.4) dizia que funções existentes
        ficavam como estavam por agora; mas quando a importação CSV
        começou a ser desenhada por outro elemento do grupo, ficou
        claro que chamar isto em loop iria poluir o terminal com
        N linhas de "adicionado com sucesso". A decisão evoluiu:
        o gestor cria e guarda; quem chama decide se imprime, mostra
        notificação visual, ou escreve num progress bar.
        Coerente com o princípio de separação de responsabilidades.
        """
        modulo = Modulo(nome, professor, horas_totais, horas_dadas, estado, datas, ufcd=ufcd)
        self.modulos.append(modulo)
        self.guardar_dados()
        return modulo

    def editar_modulo(self, nome, professor=None, horas_totais=None,
                      horas_dadas=None, estado=None, datas=None, ufcd=None,
                      sessoes=None):
        """
        Edita os campos de um módulo existente (identificado pelo nome).

        Só actualiza os campos que forem passados (diferentes de None); os
        que ficarem em None mantêm o valor actual. O **nome** é a chave e
        NÃO muda aqui de propósito: mudá-lo partiria as ligações que outras
        entidades fazem ao módulo pelo nome (formandos.modulos, avaliações,
        notas). Renomear seria uma operação à parte, mais delicada.

        Parâmetros:
            nome (str): Nome do módulo a editar (identificador).
            professor, horas_totais, horas_dadas, estado, datas, ufcd:
                novos valores (opcionais — None = não mexer).

        Retorna:
            Modulo ou None: o módulo actualizado, ou None se não existir.
        """
        modulo = self.procurar_modulo(nome)
        if modulo is None:
            return None

        if professor is not None:
            modulo.professor = professor
        if horas_totais is not None:
            modulo.horas_totais = horas_totais
        if horas_dadas is not None:
            modulo.horas_dadas = horas_dadas
        if estado is not None:
            modulo.estado = estado
        if datas is not None:
            modulo.datas = datas
        if ufcd is not None:
            modulo.ufcd = ufcd
        # Sessões (aulas com horas + "realizada"). definir_sessoes recalcula
        # sozinho as horas dadas e a lista `datas`. Se vierem sessões, é este
        # o caminho a usar (em vez de `datas`/`horas_dadas` avulsos).
        if sessoes is not None:
            modulo.definir_sessoes(sessoes)

        self.guardar_dados()
        return modulo

    def listar_modulos(self):
        """
        Mostra todos os módulos registados.
        """
        if len(self.modulos) == 0:
            print("\n  Nenhum módulo registado.")
            return

        print(f"\n  --- MÓDULOS REGISTADOS ({len(self.modulos)}) ---\n")
        contador = 0
        for m in self.modulos:
            contador = contador + 1
            print(f"  [{contador}]")
            m.mostrar_resumo()

    def procurar_modulo(self, nome):
        """
        Procura um módulo pelo nome.

        Parâmetros:
            nome (str): Nome do módulo a procurar.

        Retorna:
            Modulo ou None: O objecto se encontrado, None se não.

        Conceito: Padrão for + if com return imediato.
        Se percorrer a lista toda sem encontrar, devolve None
        (padrão return None da Sessão Online 6).
        """
        for m in self.modulos:
            if m.nome == nome:
                return m

        return None

    def modulo_existe(self, nome):
        """
        Verifica se já existe um módulo com o mesmo nome.

        Parâmetros:
            nome (str): Nome do módulo a verificar.

        Retorna:
            bool: True se já existe, False se não.

        Evolução (Sessão 3): Função criada para prevenir duplicados
        antes de adicionar (problema identificado na Sessão 2 — o
        módulo "Python Avançado" foi inserido duas vezes). Segue o
        princípio de separação de responsabilidades (secção 5.4):
        devolve bool sem print(); quem chama (main.py terminal,
        futura GUI ou importação CSV) decide como apresentar.

        Conceito: Padrão for + if com flag variable — o mesmo
        usado em Formando.esta_inscrito().
        """
        existe = False
        for m in self.modulos:
            if m.nome == nome:
                existe = True

        return existe

    def adicionar_avaliacao(self, modulo_nome, data, tipo, descricao,
                            objectivo, deliverables, peso=None):
        """
        Cria e adiciona um momento de avaliação a um módulo.

        Parâmetros:
            modulo_nome (str): Nome do módulo a avaliar.
            data, tipo, descricao, objectivo, deliverables, peso:
                campos do momento de avaliação (ver class Avaliacao).

        Retorna:
            Avaliacao ou None: O objecto criado, ou None se o módulo
                               não existir.

        Segue o mesmo padrão de adicionar_modulo (Sessão 3): o gestor
        cria, anexa e guarda; devolve o objecto sem print(). Quem chama
        (terminal hoje, GUI/HTML amanhã) decide como apresentar.
        (Sessão 4 / Bloco 2)
        """
        modulo = self.procurar_modulo(modulo_nome)
        if modulo is None:
            return None

        avaliacao = Avaliacao(data, tipo, descricao, objectivo, deliverables, peso)
        modulo.adicionar_avaliacao(avaliacao)
        self.guardar_dados()
        return avaliacao

    def editar_avaliacao(self, modulo_nome, indice, data, tipo, descricao,
                         objectivo, deliverables, peso=None):
        """
        Edita uma avaliação existente (pela posição no módulo).

        Muta o objecto Avaliacao no lugar, por isso as NOTAS já lançadas
        (`av.notas`) ficam intactas. Devolve a avaliação, ou None se o
        módulo/índice forem inválidos.
        """
        modulo = self.procurar_modulo(modulo_nome)
        if modulo is None or indice < 0 or indice >= len(modulo.avaliacoes):
            return None
        av = modulo.avaliacoes[indice]
        av.data = data
        av.tipo = tipo
        av.descricao = descricao
        av.objectivo = objectivo
        av.deliverables = deliverables
        av.peso = peso
        self.guardar_dados()
        return av

    def remover_avaliacao(self, modulo_nome, indice):
        """
        Remove uma avaliação de um módulo (pela posição), com as suas notas.

        Ao apagar, as avaliações seguintes "sobem" uma posição. Como as notas
        vivem dentro de cada avaliação, movem-se com elas — quem sincroniza
        depois reescreve os índices (avaliações + notas) de forma coerente.
        Devolve True se removeu.
        """
        modulo = self.procurar_modulo(modulo_nome)
        if modulo is None or indice < 0 or indice >= len(modulo.avaliacoes):
            return False
        del modulo.avaliacoes[indice]
        self.guardar_dados()
        return True

    def lancar_nota(self, modulo_nome, indice_avaliacao, email, nota):
        """
        Lança a nota de um aluno num instrumento de avaliação de um módulo.

        Parâmetros:
            modulo_nome (str): Nome do módulo.
            indice_avaliacao (int): Índice (0-based) da avaliação na lista
                                    de avaliações do módulo.
            email (str): Email do aluno (chave única do formando).
            nota (int ou float): Classificação obtida (escala 0-20).

        Retorna:
            bool: True se lançou; False se o módulo não existir ou o índice
                  estiver fora do intervalo das avaliações.

        Separação de responsabilidades (5.4): devolve bool, sem print.
        (Bloco 3 / Fase notas)
        """
        modulo = self.procurar_modulo(modulo_nome)
        if modulo is None:
            return False

        if indice_avaliacao < 0 or indice_avaliacao >= len(modulo.avaliacoes):
            return False

        modulo.avaliacoes[indice_avaliacao].lancar_nota(email, nota)
        self.guardar_dados()
        return True

    # ============================================================
    # PROFESSORES — Adicionar, listar, procurar
    # ============================================================

    def adicionar_professor(self, nome, email, telefone, modulos):
        """Cria e adiciona um novo professor à lista.

        Retorna:
            Professor: O objecto criado.

        Evolução (Sessão 3): Print removido para a função ser
        reutilizável por importação CSV e GUI futura sem terminal
        spam. Ver docstring de adicionar_modulo para contexto
        completo da decisão.
        """
        professor = Professor(nome, email, telefone, modulos)
        self.professores.append(professor)
        self.guardar_dados()
        return professor

    def listar_professores(self):
        """Mostra todos os professores registados."""
        if len(self.professores) == 0:
            print("\n  Nenhum professor registado.")
            return

        print(f"\n  --- PROFESSORES REGISTADOS ({len(self.professores)}) ---\n")
        for p in self.professores:
            p.mostrar_resumo()

    def procurar_professor(self, nome):
        """Procura um professor pelo nome."""
        for p in self.professores:
            if p.nome == nome:
                return p
        return None

    def procurar_professor_por_email(self, email):
        """
        Procura um professor pelo email (chave natural única).

        Usado pela autorização por papéis: quando alguém entra, é assim
        que se descobre se o email pertence a um professor (para lhe dar
        acesso só aos SEUS módulos). O email é comparado sem distinção de
        maiúsculas/minúsculas.

        Parâmetros:
            email (str): Email a procurar.

        Retorna:
            Professor ou None: o professor com esse email, ou None.
        """
        alvo = (email or "").strip().lower()
        if alvo == "":
            return None
        for p in self.professores:
            if p.email.strip().lower() == alvo:
                return p
        return None

    def professor_existe(self, email):
        """
        Verifica se já existe um professor com o mesmo email.

        Parâmetros:
            email (str): Email do professor a verificar.

        Retorna:
            bool: True se já existe, False se não.

        Evolução (Sessão 3): Função criada para prevenir duplicados
        antes de adicionar. Usa o email (e não o nome) porque,
        conforme decidido na Sessão 2 (secção 2.3), o email é a
        chave natural única — nomes podem repetir-se.

        Segue o princípio de separação de responsabilidades
        (secção 5.4): devolve bool sem print(); quem chama decide
        como apresentar.

        Conceito: Padrão for + if com flag variable.
        """
        existe = False
        for p in self.professores:
            if p.email == email:
                existe = True

        return existe

    def editar_professor(self, email, nome=None, telefone=None, modulos=None):
        """
        Edita um professor existente (identificado pelo email — a chave que
        liga o login ao papel; por isso o email NÃO muda aqui). Só actualiza
        os campos passados (não None). Devolve o professor, ou None se não
        existir.
        """
        prof = self.procurar_professor_por_email(email)
        if prof is None:
            return None
        if nome is not None:
            prof.nome = nome
        if telefone is not None:
            prof.telefone = telefone
        if modulos is not None:
            prof.modulos = modulos
        self.guardar_dados()
        return prof

    def remover_professor(self, email):
        """
        Remove um professor pelo email (chave única). Devolve True se removeu.

        Não mexe nos módulos (o campo `professor` do módulo é só um nome); o
        efeito é o professor deixar de gerir os seus módulos ao entrar.
        """
        alvo = (email or "").strip().lower()
        nova_lista = []
        removeu = False
        for p in self.professores:
            if p.email.strip().lower() == alvo:
                removeu = True
            else:
                nova_lista.append(p)
        self.professores = nova_lista
        if removeu:
            self.guardar_dados()
        return removeu

    def remover_modulo(self, nome):
        """
        Remove um módulo pelo nome (chave única). Devolve True se removeu.

        Remove o módulo e, com ele, as suas avaliações e notas (que vivem
        dentro do objecto Modulo). Limpa também a inscrição desse módulo na
        lista de módulos de cada formando, para não ficarem referências
        penduradas a um módulo que já não existe.
        """
        alvo = (nome or "").strip()
        nova_lista = []
        removeu = False
        for m in self.modulos:
            if m.nome == alvo:
                removeu = True
            else:
                nova_lista.append(m)
        self.modulos = nova_lista

        if removeu:
            # Tirar o módulo das inscrições dos formandos (padrão for + append)
            for f in self.formandos:
                if alvo in f.modulos:
                    restantes = []
                    for x in f.modulos:
                        if x != alvo:
                            restantes.append(x)
                    f.modulos = restantes
            self.guardar_dados()
        return removeu

    # ============================================================
    # FORMANDOS — Adicionar, listar
    # ============================================================

    def adicionar_formando(self, nome, email, modulos):
        """Cria e adiciona um novo formando à lista.

        Retorna:
            Formando: O objecto criado.

        Evolução (Sessão 3): Print removido. Esta é a função mais
        importante a ficar limpa porque a importação CSV em
        desenvolvimento (outro elemento do grupo) vai chamá-la em
        loop sobre dezenas de linhas — com print interno o terminal
        ficava ilegível. Ver docstring de adicionar_modulo para
        contexto completo da decisão.
        """
        formando = Formando(nome, email, modulos)
        self.formandos.append(formando)
        self.guardar_dados()
        return formando

    def editar_formando(self, email, nome=None, modulos=None):
        """
        Edita um formando existente (identificado pelo email — a chave única;
        por isso o email NÃO muda aqui). Só actualiza os campos passados (não
        None). Devolve o formando, ou None se não existir.

        Para mudar o email de um formando, remove-se e volta-se a inscrever
        (o email é a identidade do aluno, a que estão associadas as notas).
        """
        alvo = (email or "").strip().lower()
        formando = None
        for f in self.formandos:
            if f.email.strip().lower() == alvo:
                formando = f
        if formando is None:
            return None
        if nome is not None:
            formando.nome = nome
        if modulos is not None:
            formando.modulos = modulos
        self.guardar_dados()
        return formando

    def listar_formandos(self):
        """Mostra todos os formandos registados."""
        if len(self.formandos) == 0:
            print("\n  Nenhum formando registado.")
            return

        print(f"\n  --- FORMANDOS REGISTADOS ({len(self.formandos)}) ---\n")
        for f in self.formandos:
            f.mostrar_resumo()

    def formando_existe(self, email):
        """
        Verifica se já existe um formando com o mesmo email.

        Parâmetros:
            email (str): Email do formando a verificar.

        Retorna:
            bool: True se já existe, False se não.

        Evolução (Sessão 3): Função criada para prevenir duplicados
        antes de adicionar. Email é a chave única (decisão da
        Sessão 2 — secção 2.3): "Nomes podem repetir-se; email é
        único por natureza".

        Será também usada pela função de importação CSV (em
        desenvolvimento por outro elemento do grupo) para decidir
        se cada linha do CSV é um formando novo ou já existente.

        Segue o princípio de separação de responsabilidades
        (secção 5.4): devolve bool sem print().

        Conceito: Padrão for + if com flag variable.
        """
        existe = False
        for f in self.formandos:
            if f.email == email:
                existe = True

        return existe

    def remover_formando(self, email):
        """
        Remove um formando pelo email (direito ao apagamento — RGPD).

        Parâmetros:
            email (str): Email do formando a remover (chave única).

        Retorna:
            bool: True se removeu, False se não encontrou ninguém
                  com esse email.

        Contexto RGPD (secção 6): o email é um dado pessoal e o titular
        tem direito à eliminação dos seus dados. Esta função concretiza
        esse direito — estava listada como PENDENTE desde a Sessão 1.

        Implementação: padrão lista nova + for + if. Percorre os
        formandos e reconstrói a lista sem o que tem o email indicado.
        Evita remover itens durante a própria iteração (fonte clássica
        de bugs em Python).

        Separação de responsabilidades (secção 5.4): devolve bool sem
        print(); quem chama decide como apresentar.
        (Sessão 4 / Bloco 2)
        """
        nova_lista = []
        removeu = False
        for f in self.formandos:
            if f.email == email:
                removeu = True   # encontrado — NÃO o passamos para a lista nova
            else:
                nova_lista.append(f)

        self.formandos = nova_lista

        # RGPD — apagamento COMPLETO: as notas do aluno vivem dentro de cada
        # avaliação (av.notas[email]). Remover só da lista de formandos deixaria
        # as classificações para trás. Percorremos módulos -> avaliações e
        # apagamos a nota deste email onde existir.
        if removeu:
            for m in self.modulos:
                for av in m.avaliacoes:
                    if email in av.notas:
                        del av.notas[email]

        # Só gravar se houve mesmo remoção (evita reescrever ficheiro à toa)
        if removeu:
            self.guardar_dados()

        return removeu

    # ============================================================
    # ALTERAÇÕES — Registar, listar, notificar
    # ============================================================

    def registar_alteracao(self, modulo_nome, data_original, data_nova, motivo, autor):
        """
        Regista uma alteração ao cronograma e gera notificação.

        Este é o método mais importante do sistema — é aqui que
        tudo se junta:
            1. Cria o registo de alteração
            2. Identifica quem precisa de ser notificado
            3. Gera a notificação com a lista de destinatários

        Parâmetros:
            modulo_nome (str): Nome do módulo afectado.
            data_original (str): Data original.
            data_nova (str): Nova data.
            motivo (str): Razão da alteração.
            autor (str): Quem registou.

        Retorna:
            Notificacao ou None: A notificação gerada, ou None se
                                 não houver destinatários.
        """
        # 1. Criar a alteração
        alteracao = Alteracao(modulo_nome, data_original, data_nova, motivo, autor)
        self.alteracoes.append(alteracao)

        # 2. Actualizar a data no módulo (se existir)
        modulo = self.procurar_modulo(modulo_nome)
        if modulo is not None:
            # Trocar a data na sessão correspondente, preservando as horas e a
            # marca de "realizada" dessa aula. definir_sessoes volta a derivar
            # a lista `datas` a partir das sessões.
            novas_sessoes = []
            for s in modulo.sessoes:
                if s["data"] == data_original:
                    nova = dict(s)
                    nova["data"] = data_nova
                    novas_sessoes.append(nova)
                else:
                    novas_sessoes.append(s)
            modulo.definir_sessoes(novas_sessoes)

        # 3. Encontrar os destinatários
        #    — o professor do módulo + formandos inscritos
        destinatarios = []

        # Procurar o professor do módulo
        if modulo is not None:
            prof = self.procurar_professor(modulo.professor)
            if prof is not None:
                dest = {}
                dest["nome"] = prof.nome
                dest["email"] = prof.email
                destinatarios.append(dest)

        # Procurar os formandos inscritos neste módulo
        # Padrão: for + if — percorrer a lista e filtrar
        for f in self.formandos:
            if f.esta_inscrito(modulo_nome):
                dest = {}
                dest["nome"] = f.nome
                dest["email"] = f.email
                destinatarios.append(dest)

        # 4. Gerar a notificação (se houver destinatários)
        if len(destinatarios) == 0:
            print("\n  Alteração registada, mas sem destinatários para notificar.")
            self.guardar_dados()
            return None

        mensagem = alteracao.gerar_mensagem()
        notificacao = Notificacao(mensagem, destinatarios)
        self.notificacoes.append(notificacao)

        # 5. Guardar tudo
        self.guardar_dados()

        print(f"\n  Alteração registada com {len(destinatarios)} destinatários.")
        return notificacao

    def listar_alteracoes(self):
        """Mostra todas as alterações registadas."""
        if len(self.alteracoes) == 0:
            print("\n  Nenhuma alteração registada.")
            return

        print(f"\n  --- HISTÓRICO DE ALTERAÇÕES ({len(self.alteracoes)}) ---\n")
        for a in self.alteracoes:
            a.mostrar_resumo()
