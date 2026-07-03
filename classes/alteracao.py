# ============================================================
# alteracao.py — Classe Alteracao
# ============================================================
# Representa uma alteração ao cronograma — uma mudança de
# data, hora ou outra informação de um módulo.
#
# Cada alteração guarda: o que mudou, de quando para quando,
# porquê e quem fez a alteração. Funciona como um registo
# de histórico — nunca se apaga, só se acrescenta.
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários)
# ============================================================

from datetime import datetime


class Alteracao:
    """
    Representa uma alteração ao cronograma.

    Atributos:
        modulo_nome (str): Nome do módulo afectado.
        data_original (str): Data original da sessão ("dd/mm/aaaa").
        data_nova (str): Nova data da sessão ("dd/mm/aaaa").
        motivo (str): Razão da alteração (ex: "professor doente").
        autor (str): Quem registou a alteração (ex: "Coordenador").
        data_registo (str): Data e hora em que a alteração foi registada.
                            Gerada automaticamente pelo sistema.
    """

    def __init__(self, modulo_nome, data_original, data_nova, motivo, autor):
        """
        Construtor — cria um novo registo de alteração.

        A data_registo é preenchida automaticamente com a data
        e hora actuais — o utilizador não precisa de a indicar.

        Parâmetros:
            modulo_nome (str): Nome do módulo afectado.
            data_original (str): Data original.
            data_nova (str): Nova data.
            motivo (str): Razão da alteração.
            autor (str): Quem registou.
        """
        self.modulo_nome = modulo_nome
        self.data_original = data_original
        self.data_nova = data_nova
        self.motivo = motivo
        self.autor = autor

        # Data de registo gerada automaticamente
        # datetime.now() devolve a data e hora actual do sistema
        # .strftime() converte para texto no formato que queremos
        agora = datetime.now()
        self.data_registo = agora.strftime("%d/%m/%Y %H:%M")

    # --------------------------------------------------------
    # Métodos de apresentação
    # --------------------------------------------------------

    def mostrar_resumo(self):
        """
        Mostra o registo da alteração no terminal.

        Formato:
            [12/05/2026 14:30] Python Avançado
            Alteração: 14/05/2026 → 21/05/2026
            Motivo: Professor doente
            Registado por: Coordenador
        """
        print(f"  [{self.data_registo}] {self.modulo_nome}")
        print(f"  Alteração: {self.data_original} → {self.data_nova}")
        print(f"  Motivo: {self.motivo}")
        print(f"  Registado por: {self.autor}")
        print()

    def gerar_mensagem(self):
        """
        Gera o texto da notificação a enviar.

        Retorna:
            str: Mensagem formatada para enviar por email
                 ou mostrar na consola.

        Esta mensagem é usada pela classe Notificacao para
        enviar aos formandos e professores.
        """
        mensagem = (
            f"ALTERAÇÃO AO CRONOGRAMA\n"
            f"Módulo: {self.modulo_nome}\n"
            f"Data original: {self.data_original}\n"
            f"Nova data: {self.data_nova}\n"
            f"Motivo: {self.motivo}\n"
            f"Registado por: {self.autor} em {self.data_registo}\n"
        )

        return mensagem

    # --------------------------------------------------------
    # Métodos de conversão — objecto <-> dicionário (para JSON)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o objecto Alteracao num dicionário.

        Retorna:
            dict: Dicionário com todos os atributos.
        """
        dados = {}
        dados["modulo_nome"] = self.modulo_nome
        dados["data_original"] = self.data_original
        dados["data_nova"] = self.data_nova
        dados["motivo"] = self.motivo
        dados["autor"] = self.autor
        dados["data_registo"] = self.data_registo

        return dados


def alteracao_from_dict(dados):
    """
    Cria um objecto Alteracao a partir de um dicionário.

    Nota: aqui não usamos o construtor normal porque o
    construtor gera a data_registo automaticamente. Como
    estamos a reconstruir a partir do JSON, precisamos de
    manter a data original do registo.

    Parâmetros:
        dados (dict): Dicionário com as chaves da alteração.

    Retorna:
        Alteracao: Objecto Alteracao reconstruído.
    """
    alteracao = Alteracao(
        modulo_nome=dados["modulo_nome"],
        data_original=dados["data_original"],
        data_nova=dados["data_nova"],
        motivo=dados["motivo"],
        autor=dados["autor"]
    )

    # Substituir a data_registo gerada automaticamente
    # pela data que estava no JSON (a original)
    alteracao.data_registo = dados["data_registo"]

    return alteracao
