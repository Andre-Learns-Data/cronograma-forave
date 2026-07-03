// ============================================================
// calendario.js — Calendário visual (mês / semana)
// ============================================================
// Feito de raiz, sem bibliotecas externas: só JavaScript e o DOM.
// Lê os eventos que o servidor injeta em window.CAL_EVENTOS
// (aulas + avaliações) e desenha-os num calendário navegável, com
// duas vistas: MÊS e SEMANA. Usado na área do aluno (eventos dos
// módulos onde está inscrito) e na área do staff (overview dos
// módulos que o coordenador/professor vê).
//
// Porque próprio e não uma biblioteca: é código nosso (mostra
// trabalho na avaliação) e evita mais uma dependência/CDN.
//
// Convenção: a semana começa à SEGUNDA-FEIRA (como em Portugal).
// As datas dos eventos vêm em dd/mm/aaaa (formato do sistema).
// ============================================================

(function () {
    "use strict";

    var raiz = document.getElementById("calendario");
    if (!raiz) return;  // a página não tem calendário — nada a fazer

    var eventos = window.CAL_EVENTOS || [];

    var MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    var DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

    // --- Ajudantes de datas -------------------------------------------------

    // "aaaa-mm-dd" a partir de um Date — chave para agrupar eventos por dia.
    function chaveDe(d) {
        return d.getFullYear() + "-" +
               String(d.getMonth() + 1).padStart(2, "0") + "-" +
               String(d.getDate()).padStart(2, "0");
    }

    // "dd/mm/aaaa" -> Date (ou null se o formato não bater certo).
    function ddmmParaData(s) {
        var p = String(s).split("/");
        if (p.length !== 3) return null;
        var d = new Date(Number(p[2]), Number(p[1]) - 1, Number(p[0]));
        return isNaN(d.getTime()) ? null : d;
    }

    // Segunda-feira da semana de uma data (início da semana).
    function segundaDaSemana(d) {
        var x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        var desvio = (x.getDay() + 6) % 7;  // 0 = segunda ... 6 = domingo
        x.setDate(x.getDate() - desvio);
        return x;
    }

    function mesmoDia(a, b) {
        return a.getFullYear() === b.getFullYear() &&
               a.getMonth() === b.getMonth() &&
               a.getDate() === b.getDate();
    }

    // Agrupar os eventos por dia (chave 'aaaa-mm-dd') para desenho rápido.
    var porDia = {};
    eventos.forEach(function (ev) {
        var d = ddmmParaData(ev.data);
        if (!d) return;
        var k = chaveDe(d);
        if (!porDia[k]) porDia[k] = [];
        porDia[k].push(ev);
    });

    // --- Estado -------------------------------------------------------------

    var hoje = new Date();
    hoje = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
    var vista = "mes";     // "mes" | "semana"
    var ref = new Date(hoje);  // data de referência (mês/semana a mostrar)

    // --- Construção da moldura (controlos) ---------------------------------

    raiz.innerHTML =
        '<div class="cal-barra">' +
        '  <div class="cal-nav">' +
        '    <button type="button" class="btn btn-sm btn-outline-secondary" data-cal="anterior" aria-label="Anterior">&#8249;</button>' +
        '    <button type="button" class="btn btn-sm btn-outline-secondary" data-cal="hoje">Hoje</button>' +
        '    <button type="button" class="btn btn-sm btn-outline-secondary" data-cal="seguinte" aria-label="Seguinte">&#8250;</button>' +
        '    <strong class="cal-titulo ms-2"></strong>' +
        '  </div>' +
        '  <div class="btn-group btn-group-sm cal-vistas" role="group" aria-label="Vista">' +
        '    <button type="button" class="btn btn-outline-success active" data-vista="mes">Mês</button>' +
        '    <button type="button" class="btn btn-outline-success" data-vista="semana">Semana</button>' +
        '  </div>' +
        '</div>' +
        '<div class="cal-corpo"></div>' +
        '<div class="cal-legenda">' +
        '  <span class="cal-leg"><span class="cal-ponto cal-aula"></span>Aula</span>' +
        '  <span class="cal-leg"><span class="cal-ponto cal-aula-dada"></span>Aula dada</span>' +
        '  <span class="cal-leg"><span class="cal-ponto cal-avaliacao"></span>Avaliação</span>' +
        '</div>';

    var elTitulo = raiz.querySelector(".cal-titulo");
    var elCorpo = raiz.querySelector(".cal-corpo");

    // --- Desenho de um evento (chip) ---------------------------------------

    function classeEvento(ev) {
        if (ev.tipo === "avaliacao") return "cal-avaliacao";
        return ev.realizada ? "cal-aula-dada" : "cal-aula";
    }

    function textoEvento(ev) {
        if (ev.tipo === "avaliacao") return "📝 " + ev.titulo;
        return (ev.realizada ? "✓ " : "") + ev.titulo;
    }

    function criarChip(ev) {
        var chip = document.createElement("div");
        chip.className = "cal-evento " + classeEvento(ev);
        chip.textContent = textoEvento(ev);
        // Detalhe completo ao passar o rato / tocar.
        var detalhe = ev.tipo === "avaliacao"
            ? "Avaliação: " + ev.titulo + " (" + ev.modulo + ")"
            : "Aula: " + ev.modulo +
              (ev.horas ? " · " + ev.horas + "h" : "") +
              (ev.realizada ? " · já dada" : "");
        chip.title = detalhe;
        return chip;
    }

    function eventosDoDia(d) {
        return porDia[chaveDe(d)] || [];
    }

    // --- Vista MÊS ----------------------------------------------------------

    function desenharMes() {
        elTitulo.textContent = MESES[ref.getMonth()] + " " + ref.getFullYear();

        var grelha = document.createElement("div");
        grelha.className = "cal-grelha";

        // Cabeçalho com os dias da semana
        DIAS.forEach(function (nome) {
            var c = document.createElement("div");
            c.className = "cal-cabeca";
            c.textContent = nome;
            grelha.appendChild(c);
        });

        // 6 semanas × 7 dias, a começar na segunda-feira que "abre" o mês
        var inicio = segundaDaSemana(new Date(ref.getFullYear(), ref.getMonth(), 1));
        for (var i = 0; i < 42; i++) {
            var dia = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i);
            var cel = document.createElement("div");
            cel.className = "cal-dia";
            if (dia.getMonth() !== ref.getMonth()) cel.classList.add("cal-fora");
            if (mesmoDia(dia, hoje)) cel.classList.add("cal-hoje");

            var num = document.createElement("div");
            num.className = "cal-num";
            num.textContent = dia.getDate();
            cel.appendChild(num);

            var doDia = eventosDoDia(dia);
            doDia.slice(0, 3).forEach(function (ev) { cel.appendChild(criarChip(ev)); });
            if (doDia.length > 3) {
                var mais = document.createElement("div");
                mais.className = "cal-mais";
                mais.textContent = "+" + (doDia.length - 3);
                cel.appendChild(mais);
            }
            grelha.appendChild(cel);
        }

        elCorpo.innerHTML = "";
        elCorpo.appendChild(grelha);
    }

    // --- Vista SEMANA -------------------------------------------------------

    function desenharSemana() {
        var inicio = segundaDaSemana(ref);
        var fim = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + 6);
        elTitulo.textContent = "Semana de " + inicio.getDate() + " " +
            MESES[inicio.getMonth()].toLowerCase() +
            " a " + fim.getDate() + " " + MESES[fim.getMonth()].toLowerCase();

        var grelha = document.createElement("div");
        grelha.className = "cal-grelha cal-grelha-semana";

        for (var i = 0; i < 7; i++) {
            var dia = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i);
            var col = document.createElement("div");
            col.className = "cal-dia cal-dia-semana";
            if (mesmoDia(dia, hoje)) col.classList.add("cal-hoje");

            var cab = document.createElement("div");
            cab.className = "cal-cabeca-semana";
            cab.textContent = DIAS[i] + " " + dia.getDate();
            col.appendChild(cab);

            var doDia = eventosDoDia(dia);
            if (doDia.length === 0) {
                var vazio = document.createElement("div");
                vazio.className = "cal-vazio";
                vazio.textContent = "—";
                col.appendChild(vazio);
            } else {
                doDia.forEach(function (ev) { col.appendChild(criarChip(ev)); });
            }
            grelha.appendChild(col);
        }

        elCorpo.innerHTML = "";
        elCorpo.appendChild(grelha);
    }

    function desenhar() {
        if (vista === "mes") desenharMes();
        else desenharSemana();
    }

    // --- Interação ----------------------------------------------------------

    function avancar(sinal) {
        if (vista === "mes") {
            ref = new Date(ref.getFullYear(), ref.getMonth() + sinal, 1);
        } else {
            ref = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate() + 7 * sinal);
        }
        desenhar();
    }

    raiz.addEventListener("click", function (e) {
        var alvo = e.target.closest("[data-cal], [data-vista]");
        if (!alvo) return;

        if (alvo.dataset.cal === "anterior") avancar(-1);
        else if (alvo.dataset.cal === "seguinte") avancar(1);
        else if (alvo.dataset.cal === "hoje") { ref = new Date(hoje); desenhar(); }
        else if (alvo.dataset.vista) {
            vista = alvo.dataset.vista;
            raiz.querySelectorAll(".cal-vistas .btn").forEach(function (b) {
                b.classList.toggle("active", b.dataset.vista === vista);
            });
            desenhar();
        }
    });

    // Arranca na vista mês, no dia de hoje.
    desenhar();
})();
