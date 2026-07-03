# ============================================================
# auditoria.py — Classe RegistoAuditoria
# ============================================================
# Representa UMA entrada do registo de auditoria: um facto do
# tipo "quem fez o quê e quando" numa escrita da área de admin
# (adicionar módulo, adicionar avaliação, lançar notas, alterar
# o cronograma).
#
# É um registo de accountability: existe para respondermos, mais
# tarde, à pergunta "quem lançou/alterou esta nota?". Funciona
# como o histórico de alterações (Alteracao): NUNCA se apaga, só
# se acrescenta (append-only).
#
# Porque é uma classe (e não só um dicionário): mantém o mesmo
# padrão POO do resto do projecto (to_dict/from_dict), o que a
# torna fácil de gravar em JSON, no Google Sheet ou de mostrar
# numa página HTML — sem print/input aqui dentro.
#
# Alinhado com: Aula 5 (POO), Aula 6 (dicionários)
# ============================================================

from datetime import datetime


class RegistoAuditoria:
    """
    Uma entrada do registo de auditoria (append-only).

    Atributos:
        autor (str): Quem fez a acção (email do coordenador em sessão).
        accao (str): O tipo de acção (ex: "Lançar notas").
        detalhe (str): O que mudou, em texto legível (ex: o módulo,
                       a avaliação e as notas afectadas).
        data_hora (str): Data e hora do registo ("dd/mm/aaaa HH:MM").
                         Gerada automaticamente pelo sistema.
    """

    def __init__(self, autor, accao, detalhe, data_hora=None):
        """
        Construtor — cria uma entrada de auditoria.

        A data_hora é preenchida automaticamente com o momento
        actual, a menos que seja fornecida (ao reconstruir a partir
        de um registo já gravado — ver registo_from_dict).

        Parâmetros:
            autor (str): Quem fez a acção.
            accao (str): Tipo de acção.
            detalhe (str): Descrição legível do que mudou.
            data_hora (str): Opcional. Se None, usa a data/hora actual.
        """
        self.autor = autor
        self.accao = accao
        self.detalhe = detalhe

        if data_hora is None:
            agora = datetime.now()
            data_hora = agora.strftime("%d/%m/%Y %H:%M")
        self.data_hora = data_hora

    # --------------------------------------------------------
    # Conversão — objecto <-> dicionário (para JSON / Sheet / HTML)
    # --------------------------------------------------------

    def to_dict(self):
        """
        Converte o registo num dicionário.

        Retorna:
            dict: Com as chaves data_hora, autor, accao, detalhe.
        """
        return {
            "data_hora": self.data_hora,
            "autor": self.autor,
            "accao": self.accao,
            "detalhe": self.detalhe,
        }


def registo_from_dict(dados):
    """
    Cria um RegistoAuditoria a partir de um dicionário.

    É o inverso de to_dict(). Preserva a data_hora original (não
    gera uma nova), porque estamos a reconstruir um registo já feito.

    Parâmetros:
        dados (dict): Com as chaves autor, accao, detalhe, data_hora.
                      Tolerante a chaves em falta (usa "").

    Retorna:
        RegistoAuditoria: O registo reconstruído.
    """
    return RegistoAuditoria(
        autor=dados.get("autor", ""),
        accao=dados.get("accao", ""),
        detalhe=dados.get("detalhe", ""),
        data_hora=dados.get("data_hora", ""),
    )
