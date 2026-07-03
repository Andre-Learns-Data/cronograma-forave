# ============================================================
# test_web.py — Testes das rotas Flask (integração)
# ============================================================
# Páginas públicas, fluxo de registo/login, área do aluno,
# isolamento RGPD (um aluno não vê notas de outro) e endpoints
# do PWA. Corre numa pasta de dados TEMPORÁRIA — não toca nos
# dados reais (graças à variável de ambiente PASTA_DADOS).
#
# IMPORTANTE: as variáveis de ambiente têm de ser definidas ANTES
# de importar o app (o app lê-as no momento do import).
# ============================================================

import json
import os
import shutil
import tempfile
import unittest
from io import BytesIO

# Pasta temporária + modo local, ANTES de importar o app
_PASTA = tempfile.mkdtemp()
os.environ["PASTA_DADOS"] = _PASTA
os.environ["FONTE_DADOS"] = "json"
os.environ["FLASK_SECRET_KEY"] = "teste"
# Email autorizado como coordenador (para os testes da área de admin)
os.environ["COORDENADOR_EMAILS"] = "coord@forave.org"

import app as appmod  # noqa: E402
from gestor_cronograma import GestorCronograma  # noqa: E402


class TestWeb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Semear dados na pasta temporária
        g = GestorCronograma(pasta_dados=_PASTA)
        g.adicionar_modulo("Python", "Andre", 50, 30, "em curso",
                           ["01/06/2026"], ufcd="5412")
        g.adicionar_formando("Ana", "ana@forave.org", ["Python"])
        g.adicionar_formando("Rui", "rui@forave.org", ["Python"])
        g.adicionar_avaliacao("Python", "15/06/2026", "projecto",
                              "Projecto", "POO", "Repo", 70)
        g.adicionar_avaliacao("Python", "10/06/2026", "teste",
                              "Teste", "Teoria", "Folha", 30)
        g.lancar_nota("Python", 0, "ana@forave.org", 16)
        g.lancar_nota("Python", 1, "ana@forave.org", 14)
        g.lancar_nota("Python", 0, "rui@forave.org", 10)
        # Um professor (papel "professor") com um módulo só dele. bruno@ NÃO
        # está em COORDENADOR_EMAILS -> entra como professor, não coordenador.
        g.adicionar_professor("Prof Bruno", "bruno@forave.org", "", ["Modulo Bruno"])
        g.adicionar_modulo("Modulo Bruno", "Prof Bruno", 30, 0, "planeado", [])
        cls.client = appmod.app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_PASTA, ignore_errors=True)

    # --- Páginas públicas ---

    def test_landing_publica_sem_dados_do_curso(self):
        # O / é uma landing: boas-vindas + opções por perfil + ficha do curso
        # (identidade pública: CET/UFCD/professor), mas SEM dados pessoais.
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        texto = r.get_data(as_text=True)
        self.assertIn("manifest.json", texto)      # PWA
        self.assertIn("Aluno", texto)
        self.assertIn("Professor", texto)
        self.assertIn("Coordenador", texto)
        # RGPD: nada de dados PESSOAIS de alunos em público. (A identidade do
        # curso — nome/UFCD/professor — é informação pública de marketing, não
        # dado pessoal; por isso já não se testa a mera palavra "Python".)
        self.assertNotIn("@forave.org", texto)     # nenhum email de aluno
        self.assertNotIn("Rui", texto)             # nenhum nome de formando semeado

    def test_cronograma_exige_login(self):
        # Sem sessão -> redireccionado para o login
        r = self.client.get("/cronograma")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    def test_cronograma_autenticado_mostra_pagina(self):
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "ana@forave.org", "password": "segredo"},
                    follow_redirects=True)
        r = cliente.get("/cronograma")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Cockpit", r.get_data(as_text=True))  # página do cronograma

    def test_api_schedule_exige_login(self):
        # Sem sessão a API não devolve dados (redirecciona para o login)
        r = self.client.get("/api/schedule")
        self.assertEqual(r.status_code, 302)

    def test_cronograma_ics_e_publico(self):
        # Decisão 03/Jul: o horário das aulas é informação pública (não são
        # dados pessoais) -> o .ics do cronograma completo é aberto, sem login.
        r = self.client.get("/cronograma.ics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/calendar", r.headers.get("Content-Type", ""))
        self.assertIn("BEGIN:VCALENDAR", r.get_data(as_text=True))

    def test_cronograma_ics_autenticado_devolve_calendario(self):
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "ana@forave.org", "password": "segredo"},
                    follow_redirects=True)
        r = cliente.get("/cronograma.ics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/calendar", r.headers.get("Content-Type", ""))
        self.assertIn("BEGIN:VCALENDAR", r.get_data(as_text=True))

    def test_paginas_login_registo(self):
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.get("/registar").status_code, 200)

    def test_login_distingue_perfil_aluno_e_coordenador(self):
        # A entrada normal mostra "Área do Aluno"...
        aluno = self.client.get("/login").get_data(as_text=True)
        self.assertIn("Área do Aluno", aluno)
        self.assertNotIn("Área do Coordenador", aluno)
        # ...e a porta do coordenador (?perfil=coordenador) muda o título/ajuda.
        # (O papel real continua a ser decidido pelo email — isto é só visual.)
        coord = self.client.get("/login?perfil=coordenador").get_data(as_text=True)
        self.assertIn("Área do Coordenador", coord)
        self.assertIn("email de coordenação", coord)

    # --- Proteção da área do aluno ---

    def test_aluno_sem_sessao_redirecciona(self):
        r = self.client.get("/aluno")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    # --- Registo ---

    def test_registo_nao_formando_bloqueado(self):
        r = self.client.post("/registar",
                             data={"email": "estranho@gmail.com",
                                   "password": "segredo", "password2": "segredo"},
                             follow_redirects=True)
        self.assertIn("não está na lista de formandos", r.get_data(as_text=True))

    # --- Fluxo completo + RGPD ---

    def test_fluxo_login_e_notas_e_rgpd(self):
        cliente = appmod.app.test_client()
        # Registar a Ana (formanda válida)
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        # Login
        r = cliente.post("/login",
                        data={"email": "ana@forave.org", "password": "segredo"},
                        follow_redirects=True)
        texto = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        # Vê a sua nota final ponderada (15.4) e as notas individuais
        self.assertIn("15.4", texto)
        self.assertIn("16", texto)
        self.assertIn("14", texto)
        # RGPD: NÃO vê dados de outro aluno
        self.assertNotIn("Rui", texto)

    def test_login_errado(self):
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        r = cliente.post("/login",
                        data={"email": "ana@forave.org", "password": "errada"},
                        follow_redirects=True)
        self.assertIn("incorrectos", r.get_data(as_text=True))

    # --- Reposição de password ("esqueci-me") ---

    def test_recuperar_resposta_neutra(self):
        # A página existe e o pedido responde sempre com mensagem neutra
        # (não revela se o email tem conta).
        self.assertEqual(self.client.get("/recuperar").status_code, 200)
        r = self.client.post("/recuperar",
                             data={"email": "qualquer@forave.org"},
                             follow_redirects=True)
        self.assertIn("link de reposição", r.get_data(as_text=True))

    def test_repor_token_invalido_redirecciona(self):
        r = self.client.get("/repor/token-invalido")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/recuperar", r.headers.get("Location", ""))

    def test_fluxo_reposicao_muda_password(self):
        cliente = appmod.app.test_client()
        # Usar o Rui (formando válido semeado, sem conta noutro teste).
        # Registar é idempotente — se já existir, a rota só segue em frente.
        cliente.post("/registar",
                    data={"email": "rui@forave.org",
                          "password": "antiga1", "password2": "antiga1"},
                    follow_redirects=True)
        # O email não está configurado nos testes, por isso geramos o token
        # directamente (mesma secret_key do app) e seguimos o link.
        token = appmod.carregar_auth().criar_token_reposicao("rui@forave.org")
        self.assertIsNotNone(token)

        # O link mostra o formulário
        self.assertEqual(cliente.get("/repor/" + token).status_code, 200)

        # Definir a nova password
        r = cliente.post("/repor/" + token,
                        data={"password": "nova123", "password2": "nova123"},
                        follow_redirects=True)
        self.assertIn("actualizada", r.get_data(as_text=True))

        # A antiga já não entra; a nova entra
        r_velha = cliente.post("/login",
                              data={"email": "rui@forave.org", "password": "antiga1"},
                              follow_redirects=True)
        self.assertIn("incorrectos", r_velha.get_data(as_text=True))
        r_nova = cliente.post("/login",
                             data={"email": "rui@forave.org", "password": "nova123"},
                             follow_redirects=True)
        self.assertEqual(r_nova.status_code, 200)

    def test_recuperar_nao_rebenta_se_email_falha(self):
        # Simula um envio de email que rebenta (ex.: SMTP bloqueado no
        # alojamento gratuito): a página TEM de continuar a responder
        # normalmente com a mensagem neutra, nunca dar erro 500.
        def email_rebenta():
            raise RuntimeError("SMTP bloqueado (simulado)")

        original = appmod.carregar_email
        appmod.carregar_email = email_rebenta
        try:
            cliente = appmod.app.test_client()
            # Garantir uma conta registada (token != None -> entra no envio)
            cliente.post("/registar",
                        data={"email": "ana@forave.org",
                              "password": "segredo", "password2": "segredo"},
                        follow_redirects=True)
            r = cliente.post("/recuperar",
                            data={"email": "ana@forave.org"},
                            follow_redirects=True)
            self.assertEqual(r.status_code, 200)
            self.assertIn("link de reposição", r.get_data(as_text=True))
        finally:
            appmod.carregar_email = original

    # --- Área de administração (coordenador) ---

    def _cliente_coordenador(self):
        """Regista e autentica o coordenador; devolve o cliente com sessão."""
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "coord@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "coord@forave.org", "password": "segredo"},
                    follow_redirects=True)
        return cliente

    def test_admin_sem_sessao_redirecciona(self):
        r = self.client.get("/admin")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    def test_admin_aluno_nao_entra(self):
        # Ana é aluna (não está em COORDENADOR_EMAILS) -> não acede à admin
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "ana@forave.org", "password": "segredo"},
                    follow_redirects=True)
        r = cliente.get("/admin")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    def test_coordenador_entra_e_ve_painel(self):
        cliente = self._cliente_coordenador()
        r = cliente.get("/admin")
        self.assertEqual(r.status_code, 200)
        texto = r.get_data(as_text=True)
        self.assertIn("Administração", texto)
        self.assertIn("Python", texto)  # módulo semeado

    def test_admin_adiciona_modulo(self):
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Base de Dados", "ufcd": "0709",
                          "professor": "Rita", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "25",
                          "datas": "10/09/2026"},
                    follow_redirects=True)
        r = cliente.get("/admin")
        self.assertIn("Base de Dados", r.get_data(as_text=True))

    def test_admin_lanca_nota(self):
        cliente = self._cliente_coordenador()
        # Lança 19 ao Rui na avaliação 0 do módulo Python (as notas do Rui
        # não são verificadas por nenhum outro teste — evita interferência)
        cliente.post("/admin/nota",
                    data={"modulo": "Python", "indice": "0",
                          "nota__rui@forave.org": "19"},
                    follow_redirects=True)
        # O Rui, autenticado, passa a ver 19 nas suas notas
        aluno = appmod.app.test_client()
        aluno.post("/registar",
                  data={"email": "rui@forave.org",
                        "password": "segredo", "password2": "segredo"},
                  follow_redirects=True)
        aluno.post("/login",
                  data={"email": "rui@forave.org", "password": "segredo"},
                  follow_redirects=True)
        r = aluno.get("/aluno")
        self.assertIn("19", r.get_data(as_text=True))

    def test_admin_lanca_nota_com_aviso_nao_rebenta(self):
        # Lançar com "avisar cada aluno" marcado: sem email configurado nos
        # testes não envia nada, mas a rota responde bem (200) e grava a nota.
        cliente = self._cliente_coordenador()
        r = cliente.post("/admin/nota",
                        data={"modulo": "Python", "indice": "0",
                              "avisar_notas": "on",
                              "nota__rui@forave.org": "13"},
                        follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertEqual(
            g.procurar_modulo("Python").avaliacoes[0].obter_nota("rui@forave.org"), 13)

    def test_admin_adiciona_avaliacao_com_aviso_nao_rebenta(self):
        # "Avisar a turma" marcado + data: sem email configurado nos testes não
        # envia nada, mas a rota responde bem (200) e cria a avaliação.
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Mod Aval Aviso", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10",
                          "datas": "01/01/2026"},
                    follow_redirects=True)
        r = cliente.post("/admin/avaliacao",
                        data={"modulo": "Mod Aval Aviso", "descricao": "Teste X",
                              "data": "20/06/2026", "avisar": "on"},
                        follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        avs = g.procurar_modulo("Mod Aval Aviso").avaliacoes
        self.assertEqual(len(avs), 1)
        self.assertEqual(avs[0].descricao, "Teste X")

    def test_admin_avaliacao_data_iso_guardada_em_ddmm(self):
        # O calendário envia a data em ISO (aaaa-mm-dd); deve ser guardada no
        # formato do sistema (dd/mm/aaaa), pela conversão na rota.
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Mod Aval ISO", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10",
                          "datas": "01/01/2026"},
                    follow_redirects=True)
        cliente.post("/admin/avaliacao",
                    data={"modulo": "Mod Aval ISO", "descricao": "T",
                          "data": "2026-06-20"},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertEqual(
            g.procurar_modulo("Mod Aval ISO").avaliacoes[0].data, "20/06/2026")

    def test_admin_muda_cronograma(self):
        cliente = self._cliente_coordenador()
        # Módulo dedicado (evita interferir com os outros testes)
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Alteracao", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10",
                          "datas": "01/01/2026"},
                    follow_redirects=True)
        # Mudar a data (sem avisar por email)
        cliente.post("/admin/alteracao",
                    data={"modulo": "Modulo Alteracao",
                          "data_original": "01/01/2026",
                          "data_nova": "02/02/2026",
                          "motivo": "teste"},
                    follow_redirects=True)
        # Confirmar na fonte de dados local
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        m = g.procurar_modulo("Modulo Alteracao")
        self.assertIn("02/02/2026", m.datas)
        self.assertNotIn("01/01/2026", m.datas)
        self.assertTrue(any(a.modulo_nome == "Modulo Alteracao" for a in g.alteracoes))

    # --- Papel "professor" (âmbito por módulo) ---

    def _cliente_professor(self):
        """Regista e autentica o professor Bruno; devolve o cliente."""
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "bruno@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "bruno@forave.org", "password": "segredo"},
                    follow_redirects=True)
        return cliente

    def test_professor_ve_so_o_seu_modulo(self):
        cliente = self._cliente_professor()
        r = cliente.get("/admin")
        self.assertEqual(r.status_code, 200)
        texto = r.get_data(as_text=True)
        self.assertIn("Área do Professor", texto)
        self.assertIn("Modulo Bruno", texto)   # o módulo dele
        self.assertNotIn("Python", texto)      # não vê módulos de outros
        # Também não tem os formulários de coordenador nem o registo global
        self.assertNotIn("Importar módulos por CSV", texto)
        self.assertNotIn("Registo de alterações", texto)

    def test_professor_nao_adiciona_modulo(self):
        cliente = self._cliente_professor()
        cliente.post("/admin/modulo",
                    data={"nome": "Intruso", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertIsNone(g.procurar_modulo("Intruso"))  # bloqueado

    def test_professor_nao_edita_modulo_de_outro(self):
        cliente = self._cliente_professor()
        cliente.post("/admin/modulo/editar",
                    data={"nome": "Python", "professor": "Hacker",
                          "estado": "em curso", "horas_dadas": "0",
                          "horas_totais": "50", "datas": ""},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertNotEqual(g.procurar_modulo("Python").professor, "Hacker")

    def test_professor_edita_o_seu_modulo(self):
        cliente = self._cliente_professor()
        cliente.post("/admin/modulo/editar",
                    data={"nome": "Modulo Bruno", "professor": "Prof Bruno",
                          "estado": "em curso", "horas_dadas": "5",
                          "horas_totais": "30", "datas": ""},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertEqual(g.procurar_modulo("Modulo Bruno").estado, "em curso")

    def test_admin_inscreve_e_remove_formando_rgpd(self):
        cliente = self._cliente_coordenador()
        # Inscrever um formando dedicado
        cliente.post("/admin/formando",
                    data={"nome": "Formando Novo", "email": "novo@forave.org",
                          "modulos": ["Python"]},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertTrue(g.formando_existe("novo@forave.org"))
        # Remover (direito ao apagamento — RGPD)
        cliente.post("/admin/formando/remover",
                    data={"email": "novo@forave.org"},
                    follow_redirects=True)
        g2 = GestorCronograma(pasta_dados=_PASTA)
        g2.carregar_dados()
        self.assertFalse(g2.formando_existe("novo@forave.org"))

    def test_admin_edita_formando(self):
        # O coordenador edita o nome e os módulos de um formando (email = chave)
        cliente = self._cliente_coordenador()
        cliente.post("/admin/formando",
                    data={"nome": "Formando Edit", "email": "fedit@forave.org",
                          "modulos": ["Python"]},
                    follow_redirects=True)
        cliente.post("/admin/formando/editar",
                    data={"email": "fedit@forave.org", "nome": "Formando Editado",
                          "modulos": ["Modulo Bruno"]},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        alvo = None
        for f in g.formandos:
            if f.email == "fedit@forave.org":
                alvo = f
        self.assertIsNotNone(alvo)
        self.assertEqual(alvo.nome, "Formando Editado")
        self.assertEqual(alvo.modulos, ["Modulo Bruno"])

    def test_admin_descarregar_auditoria_csv(self):
        # O registo de alterações completo pode ser descarregado em CSV
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Audit CSV", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        r = cliente.get("/admin/auditoria.csv")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r.headers.get("Content-Type", ""))
        texto = r.get_data(as_text=True)
        self.assertIn("data_hora", texto)       # linha de cabeçalho
        self.assertIn("Modulo Audit CSV", texto)  # a ação ficou no registo

    def test_admin_edita_e_remove_avaliacao(self):
        cliente = self._cliente_coordenador()
        # Módulo + avaliação dedicados (não mexe no "Python" partilhado)
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Aval", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        cliente.post("/admin/avaliacao",
                    data={"modulo": "Modulo Aval", "data": "01/01/2026",
                          "tipo": "teste", "descricao": "Original",
                          "objectivo": "o", "deliverables": "d", "peso": "50"},
                    follow_redirects=True)
        # Editar
        cliente.post("/admin/avaliacao/editar",
                    data={"modulo": "Modulo Aval", "indice": "0",
                          "data": "02/02/2026", "tipo": "projeto",
                          "descricao": "Editada", "objectivo": "o2",
                          "deliverables": "d2", "peso": "70"},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        av = g.procurar_modulo("Modulo Aval").avaliacoes[0]
        self.assertEqual(av.descricao, "Editada")
        self.assertEqual(av.peso, 70)
        # Remover
        cliente.post("/admin/avaliacao/remover",
                    data={"modulo": "Modulo Aval", "indice": "0"},
                    follow_redirects=True)
        g2 = GestorCronograma(pasta_dados=_PASTA)
        g2.carregar_dados()
        self.assertEqual(len(g2.procurar_modulo("Modulo Aval").avaliacoes), 0)

    def test_admin_edita_e_remove_professor(self):
        cliente = self._cliente_coordenador()
        # Professor temporário (não toca no "Prof Bruno" semeado)
        cliente.post("/admin/professor",
                    data={"nome": "Prof Temp", "email": "temp@forave.org",
                          "telefone": "", "modulos": ["Python"]},
                    follow_redirects=True)
        # Editar: novo nome, telefone e módulos
        cliente.post("/admin/professor/editar",
                    data={"email": "temp@forave.org", "nome": "Prof Temp 2",
                          "telefone": "911111111", "modulos": ["Modulo Bruno"]},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        prof = g.procurar_professor_por_email("temp@forave.org")
        self.assertEqual(prof.nome, "Prof Temp 2")
        self.assertEqual(prof.modulos, ["Modulo Bruno"])
        # Remover
        cliente.post("/admin/professor/remover",
                    data={"email": "temp@forave.org"}, follow_redirects=True)
        g2 = GestorCronograma(pasta_dados=_PASTA)
        g2.carregar_dados()
        self.assertIsNone(g2.procurar_professor_por_email("temp@forave.org"))

    def test_coordenador_cria_professor_web_e_professor_entra(self):
        # Coordenador cria a professora Carla e associa-lhe o módulo "Python"
        coord = self._cliente_coordenador()
        coord.post("/admin/professor",
                  data={"nome": "Prof Carla", "email": "carla@forave.org",
                        "telefone": "", "modulos": ["Python"]},
                  follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        prof = g.procurar_professor_por_email("carla@forave.org")
        self.assertIsNotNone(prof)
        self.assertIn("Python", prof.modulos)
        # A Carla regista-se e entra -> papel professor, vê o módulo dela
        carla = appmod.app.test_client()
        carla.post("/registar",
                  data={"email": "carla@forave.org",
                        "password": "segredo", "password2": "segredo"},
                  follow_redirects=True)
        r = carla.post("/login",
                      data={"email": "carla@forave.org", "password": "segredo"},
                      follow_redirects=True)
        texto = r.get_data(as_text=True)
        self.assertIn("Área do Professor", texto)
        self.assertIn("Python", texto)  # o módulo associado

    def test_admin_editar_modulo(self):
        cliente = self._cliente_coordenador()
        # Cria um módulo dedicado e depois edita-o pela web
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Editar", "estado": "planeado",
                          "professor": "Ze", "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        cliente.post("/admin/modulo/editar",
                    data={"nome": "Modulo Editar", "professor": "Rita",
                          "ufcd": "0709", "estado": "em curso",
                          "horas_dadas": "5", "horas_totais": "20"},
                    follow_redirects=True)
        # Confirmar na fonte de dados local que os campos mudaram
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        m = g.procurar_modulo("Modulo Editar")
        self.assertEqual(m.professor, "Rita")
        self.assertEqual(m.ufcd, "0709")
        self.assertEqual(m.estado, "em curso")
        self.assertEqual(m.horas_totais, 20)
        # Editar NÃO mexe nas datas (geridas na subsecção Cronograma)
        self.assertEqual(m.datas, [])

    def test_admin_definir_datas(self):
        # O cronograma envia-se em JSON (sessões: data + horas + "realizada").
        # As datas derivam das sessões; as horas dadas somam as aulas dadas.
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Datas", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        sessoes = ('[{"data":"09/06/2026","horas":3,"realizada":true},'
                   '{"data":"16/06/2026","horas":2,"realizada":false}]')
        cliente.post("/admin/modulo/datas",
                    data={"nome": "Modulo Datas", "sessoes": sessoes},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        m = g.procurar_modulo("Modulo Datas")
        self.assertEqual(m.datas, ["09/06/2026", "16/06/2026"])
        self.assertEqual(m.horas_dadas, 3)  # só a aula de 3h está marcada como dada

    def test_admin_definir_datas_horas_calculadas(self):
        # A marca de "aula dada" faz as horas contarem: horas dadas = soma das
        # horas das aulas marcadas; horas em falta = totais - dadas.
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Horas", "estado": "em curso",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        sessoes = ('[{"data":"05/05/2026","horas":4,"realizada":true},'
                   '{"data":"12/05/2026","horas":4,"realizada":true}]')
        r = cliente.post("/admin/modulo/datas",
                        data={"nome": "Modulo Horas", "sessoes": sessoes},
                        follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        m = g.procurar_modulo("Modulo Horas")
        self.assertEqual(m.datas, ["05/05/2026", "12/05/2026"])
        self.assertEqual(m.horas_dadas, 8)
        self.assertEqual(m.horas_restantes(), 2)

    def test_admin_importar_csv_com_datas(self):
        cliente = self._cliente_coordenador()
        csv = ("nome,professor,horas_totais,horas_dadas,estado,datas\n"
               "Modulo CSV,Rita,40,0,planeado,01/09/2026;08/09/2026\n")
        r = cliente.post("/admin/importar_csv",
                         data={"csv": (BytesIO(csv.encode("utf-8")), "modulos.csv")},
                         content_type="multipart/form-data",
                         follow_redirects=True)
        texto = r.get_data(as_text=True)
        self.assertIn("Importação:", texto)
        self.assertIn("Modulo CSV", texto)  # aparece no painel
        # Ficou na fonte de dados local, já com as datas (o cronograma)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        m = g.procurar_modulo("Modulo CSV")
        self.assertIsNotNone(m)
        self.assertEqual(m.datas, ["01/09/2026", "08/09/2026"])

    def test_admin_importar_formandos_csv(self):
        # Importação de FORMANDOS por CSV (o motor já existia; agora está na web)
        cliente = self._cliente_coordenador()
        csv = ("nome,email,modulos\n"
               "Formando CSV,fcsv@forave.org,Python\n")
        r = cliente.post("/admin/importar_csv_formandos",
                         data={"csv": (BytesIO(csv.encode("utf-8")), "formandos.csv")},
                         content_type="multipart/form-data",
                         follow_redirects=True)
        self.assertIn("Importação:", r.get_data(as_text=True))
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertTrue(g.formando_existe("fcsv@forave.org"))

    def test_admin_importar_professores_csv(self):
        # Importação de PROFESSORES por CSV pela web
        cliente = self._cliente_coordenador()
        csv = ("nome,email,telefone,modulos\n"
               "Prof CSV,pcsv@forave.org,912345678,Python\n")
        r = cliente.post("/admin/importar_csv_professores",
                         data={"csv": (BytesIO(csv.encode("utf-8")), "professores.csv")},
                         content_type="multipart/form-data",
                         follow_redirects=True)
        self.assertIn("Importação:", r.get_data(as_text=True))
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertIsNotNone(g.procurar_professor_por_email("pcsv@forave.org"))

    def test_admin_remove_modulo(self):
        # O coordenador remove um módulo (com as suas avaliações/notas)
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo A Remover", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertIsNotNone(g.procurar_modulo("Modulo A Remover"))
        # Remover
        cliente.post("/admin/modulo/remover",
                    data={"nome": "Modulo A Remover"}, follow_redirects=True)
        g2 = GestorCronograma(pasta_dados=_PASTA)
        g2.carregar_dados()
        self.assertIsNone(g2.procurar_modulo("Modulo A Remover"))

    def test_professor_nao_remove_modulo(self):
        # Remover módulo é reservado ao coordenador -> o professor é bloqueado
        cliente = self._cliente_professor()
        cliente.post("/admin/modulo/remover",
                    data={"nome": "Modulo Bruno"}, follow_redirects=True)
        g = GestorCronograma(pasta_dados=_PASTA)
        g.carregar_dados()
        self.assertIsNotNone(g.procurar_modulo("Modulo Bruno"))  # continua lá

    # --- Auditoria (accountability das escritas da admin) ---

    def test_auditoria_regista_lancamento_de_nota(self):
        cliente = self._cliente_coordenador()
        # Lança uma nota ao Rui (avaliação 1, valor 17)
        cliente.post("/admin/nota",
                    data={"modulo": "Python", "indice": "1",
                          "nota__rui@forave.org": "17"},
                    follow_redirects=True)
        # O painel da admin passa a mostrar a entrada de auditoria:
        # acção, autor (coordenador) e o detalhe granular (email=valor)
        r = cliente.get("/admin")
        texto = r.get_data(as_text=True)
        self.assertIn("Registo de alterações", texto)
        self.assertIn("Lançar notas", texto)
        self.assertIn("coord@forave.org", texto)
        # Detalhe com o valor anterior -> novo (rui não tinha nota na avaliação 1)
        self.assertIn("rui@forave.org: —→17", texto)

    def test_auditoria_persistida_no_ficheiro_local(self):
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Auditado", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        # Em modo local (json), a auditoria vive em dados/auditoria.json
        caminho = os.path.join(_PASTA, "auditoria.json")
        self.assertTrue(os.path.exists(caminho))
        with open(caminho, "r", encoding="utf-8") as f:
            registos = json.load(f)
        # Existe uma entrada "Adicionar módulo" para o módulo criado
        self.assertTrue(any(
            e["accao"] == "Adicionar módulo" and "Modulo Auditado" in e["detalhe"]
            and e["autor"] == "coord@forave.org"
            for e in registos
        ))

    def test_auditoria_nota_mostra_valor_anterior(self):
        # Lançar 10 e depois 15 no mesmo aluno -> a auditoria mostra "10→15"
        cliente = self._cliente_coordenador()
        cliente.post("/admin/modulo",
                    data={"nome": "Modulo Nota", "estado": "planeado",
                          "horas_dadas": "0", "horas_totais": "10"},
                    follow_redirects=True)
        cliente.post("/admin/formando",
                    data={"nome": "Aluno Nota", "email": "aluno.nota@forave.org",
                          "modulos": ["Modulo Nota"]},
                    follow_redirects=True)
        cliente.post("/admin/avaliacao",
                    data={"modulo": "Modulo Nota", "descricao": "AvNota", "peso": "100"},
                    follow_redirects=True)
        cliente.post("/admin/nota",
                    data={"modulo": "Modulo Nota", "indice": "0",
                          "nota__aluno.nota@forave.org": "10"},
                    follow_redirects=True)
        cliente.post("/admin/nota",
                    data={"modulo": "Modulo Nota", "indice": "0",
                          "nota__aluno.nota@forave.org": "15"},
                    follow_redirects=True)
        r = cliente.get("/admin")
        self.assertIn("aluno.nota@forave.org: 10→15", r.get_data(as_text=True))

    # --- QR / .ics por módulo (Bloco D) ---

    def _cliente_aluno(self):
        """Regista e autentica a Ana; devolve o cliente com sessão."""
        cliente = appmod.app.test_client()
        cliente.post("/registar",
                    data={"email": "ana@forave.org",
                          "password": "segredo", "password2": "segredo"},
                    follow_redirects=True)
        cliente.post("/login",
                    data={"email": "ana@forave.org", "password": "segredo"},
                    follow_redirects=True)
        return cliente

    def test_qr_login_e_publico_e_devolve_png(self):
        # O QR de login é público (aponta só ao ecrã de entrada) e é um PNG.
        # Já não vai na landing, mas o endpoint existe (cartaz/slide).
        r = self.client.get("/qr-login.png")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image/png", r.headers.get("Content-Type", ""))
        self.assertEqual(r.get_data()[:8], b"\x89PNG\r\n\x1a\n")

    def test_qr_cronograma_publico_devolve_png(self):
        # O QR do cronograma completo é público (aponta ao .ics público) e PNG.
        r = self.client.get("/qr-cronograma.png")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image/png", r.headers.get("Content-Type", ""))
        self.assertEqual(r.get_data()[:8], b"\x89PNG\r\n\x1a\n")

    def test_landing_tem_seccao_cronograma(self):
        # C na landing: a secção "Adicionar ao calendário" (botão + QR) aparece.
        texto = self.client.get("/").get_data(as_text=True)
        self.assertIn("qr-cronograma.png", texto)
        self.assertIn("cronograma.ics", texto)

    def test_modulo_ics_por_nome_exige_login(self):
        # Sem sessão e sem token -> redirecciona para o login (RGPD).
        r = self.client.get("/modulo.ics?nome=Python")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    def test_modulo_ics_autenticado_devolve_so_esse_modulo(self):
        cliente = self._cliente_aluno()
        r = cliente.get("/modulo.ics?nome=Python")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/calendar", r.headers.get("Content-Type", ""))
        texto = r.get_data(as_text=True)
        self.assertIn("BEGIN:VCALENDAR", texto)
        self.assertIn("Python", texto)          # o módulo pedido
        self.assertIn("BEGIN:VEVENT", texto)    # tem 1 data -> 1 evento
        self.assertNotIn("Modulo Bruno", texto)  # não traz outros módulos

    def test_modulo_ics_por_token_funciona_sem_sessao(self):
        # O cenário do QR: telemóvel abre o link (com token) sem sessão.
        token = appmod.criar_token_modulo("Python", appmod.app.secret_key)
        r = self.client.get("/modulo.ics?t=" + token)
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/calendar", r.headers.get("Content-Type", ""))
        self.assertIn("BEGIN:VCALENDAR", r.get_data(as_text=True))

    def test_modulo_ics_token_invalido_da_403(self):
        r = self.client.get("/modulo.ics?t=token-falsificado")
        self.assertEqual(r.status_code, 403)

    def test_modulo_ics_nome_inexistente_da_404(self):
        cliente = self._cliente_aluno()
        r = cliente.get("/modulo.ics?nome=NaoExiste")
        self.assertEqual(r.status_code, 404)

    def test_modulo_qr_exige_login(self):
        r = self.client.get("/modulo/qr.png?nome=Python")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers.get("Location", ""))

    def test_modulo_qr_autenticado_devolve_png(self):
        cliente = self._cliente_aluno()
        r = cliente.get("/modulo/qr.png?nome=Python")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image/png", r.headers.get("Content-Type", ""))
        self.assertEqual(r.get_data()[:8], b"\x89PNG\r\n\x1a\n")

    def test_modulo_qr_nome_inexistente_da_404(self):
        cliente = self._cliente_aluno()
        r = cliente.get("/modulo/qr.png?nome=NaoExiste")
        self.assertEqual(r.status_code, 404)

    # --- PWA ---

    def test_pwa_endpoints(self):
        sw = self.client.get("/sw.js")
        self.assertEqual(sw.status_code, 200)
        self.assertIn("javascript", sw.headers.get("Content-Type", ""))
        man = self.client.get("/static/manifest.json")
        self.assertEqual(man.status_code, 200)

    # --- Segurança e páginas de erro ---

    def test_pagina_404_com_marca(self):
        # Um endereço inexistente devolve 404 com a página da marca (não a feia
        # por omissão do Flask).
        r = self.client.get("/rota-que-nao-existe-123")
        self.assertEqual(r.status_code, 404)
        texto = r.get_data(as_text=True)
        self.assertIn("404", texto)
        self.assertIn("Voltar ao início", texto)

    def test_cabecalhos_de_seguranca(self):
        # Todas as respostas trazem os cabeçalhos de segurança padrão.
        r = self.client.get("/")
        self.assertEqual(r.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(r.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertIn("Referrer-Policy", r.headers)


class TestConversaoDatas(unittest.TestCase):
    """Conversao de datas entre o calendario (ISO) e o formato do sistema.

    Os campos <input type="date"> enviam/recebem datas em aaaa-mm-dd, mas o
    sistema guarda e mostra em dd/mm/aaaa. Estas duas funcoes fazem a ponte nos
    dois sentidos sem partir a consistencia das datas.
    """

    def test_iso_para_ddmm(self):
        self.assertEqual(appmod._data_form_para_ddmm("2026-06-16"), "16/06/2026")
        self.assertEqual(appmod._data_form_para_ddmm("  2026-01-05 "), "05/01/2026")

    def test_ja_em_ddmm_nao_muda(self):
        self.assertEqual(appmod._data_form_para_ddmm("16/06/2026"), "16/06/2026")

    def test_vazio_e_invalido_sao_preservados(self):
        self.assertEqual(appmod._data_form_para_ddmm(""), "")
        self.assertEqual(appmod._data_form_para_ddmm("lixo"), "lixo")

    def test_filtro_ddmm_para_iso(self):
        self.assertEqual(appmod._data_iso("16/06/2026"), "2026-06-16")
        self.assertEqual(appmod._data_iso("5/6/2026"), "2026-06-05")

    def test_filtro_invalido_devolve_vazio(self):
        self.assertEqual(appmod._data_iso(""), "")
        self.assertEqual(appmod._data_iso("2026-06-16"), "")
        self.assertEqual(appmod._data_iso("lixo"), "")

    def test_roundtrip(self):
        iso = "2026-06-16"
        self.assertEqual(appmod._data_iso(appmod._data_form_para_ddmm(iso)), iso)


if __name__ == "__main__":
    unittest.main()
