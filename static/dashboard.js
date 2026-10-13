// ============================================================
// dashboard.js — Widgets da "Visão geral" (Administração)
// ============================================================
// Lê dois globais já colocados pelo template:
//   window.VIZ_MODULOS  — módulos (só campos NÃO pessoais)
//   window.CAL_EVENTOS  — aulas + avaliações com data (dd/mm/aaaa)
// e desenha: próximas aulas/avaliações, alertas de atenção, e dois
// gráficos (progresso por módulo + estado dos módulos).
//
// Porquê aqui e não no forave.js: isto é específico da dashboard e
// precisa que os dados (e o Chart.js) já estejam carregados — por isso
// o template carrega este ficheiro DEPOIS dos globais e do Chart.js.
//
// Paleta validada (script de dataviz): o verde FORAVE para as barras
// (série única, muito legível) e, para os estados, um trio semântico
// concluído=verde / em curso=âmbar / planeado=cinza — com rótulos e
// legenda, por isso a cor nunca é o único sinal.
// ============================================================
(function () {
    "use strict";

    // Só corre na página que tem a dashboard.
    var sec = document.getElementById("sec-visao");
    if (!sec) return;

    var VERDE_FORAVE = "#196141";
    var ESTADOS = {
        "concluido": { cor: "#1a7a3a", rotulo: "Concluído" },
        "em curso":  { cor: "#c77f0a", rotulo: "Em curso" },
        "planeado":  { cor: "#8a95a3", rotulo: "Planeado" }
    };
    var ORDEM_ESTADOS = ["concluido", "em curso", "planeado"];
    var MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
                 "jul", "ago", "set", "out", "nov", "dez"];

    var mods = window.VIZ_MODULOS || [];
    var eventos = window.CAL_EVENTOS || [];

    // Escapa texto antes de o meter em innerHTML (os nomes vêm de dados).
    function escapar(s) {
        return String(s === undefined || s === null ? "" : s)
            .replace(/[&<>"']/g, function (c) {
                return { "&": "&amp;", "<": "&lt;", ">": "&gt;",
                         '"': "&quot;", "'": "&#39;" }[c];
            });
    }

    // dd/mm/aaaa -> objeto Date (ou null se a data não estiver preenchida).
    function paraData(d) {
        var p = (d || "").split("/");
        if (p.length !== 3) return null;
        return new Date(parseInt(p[2], 10), parseInt(p[1], 10) - 1, parseInt(p[0], 10));
    }

    function normalizarEstado(e) {
        e = (e || "").toLowerCase().trim();
        if (e.indexOf("conclu") >= 0) return "concluido";
        if (e.indexOf("curso") >= 0) return "em curso";
        return "planeado";
    }

    // ---- Próximas aulas e avaliações -------------------------------------
    (function proximas() {
        var ul = document.getElementById("proximasEventos");
        if (!ul) return;

        var hoje = new Date();
        hoje.setHours(0, 0, 0, 0);

        var futuros = [];
        for (var i = 0; i < eventos.length; i++) {
            var dt = paraData(eventos[i].data);
            if (dt && dt >= hoje) {
                var e = eventos[i];
                futuros.push({ _d: dt, tipo: e.tipo, titulo: e.titulo,
                               modulo: e.modulo, horas: e.horas });
            }
        }
        futuros.sort(function (a, b) { return a._d - b._d; });
        futuros = futuros.slice(0, 6);

        if (!futuros.length) {
            ul.innerHTML = '<li class="app-vazio">Sem aulas ou avaliações agendadas para os próximos dias.</li>';
            return;
        }

        var html = "";
        for (var j = 0; j < futuros.length; j++) {
            var ev = futuros[j];
            var aval = (ev.tipo === "avaliacao");
            var icon = aval ? "bi-clipboard-check" : "bi-easel";
            var extra = ev.horas ? (" · " + ev.horas + "h") : "";
            html +=
                '<li>' +
                '<span class="app-data-bloco ' + (aval ? "is-aval" : "is-aula") + '">' +
                    '<span class="dia">' + ev._d.getDate() + '</span>' +
                    '<span class="mes">' + MESES[ev._d.getMonth()] + '</span>' +
                '</span>' +
                '<span class="app-prox-corpo">' +
                    '<span class="titulo"><i class="bi ' + icon + ' me-1"></i>' + escapar(ev.titulo) + '</span>' +
                    '<span class="sub">' + escapar(ev.modulo) + extra + '</span>' +
                '</span>' +
                '<span class="app-etiqueta ' + (aval ? "is-aval" : "is-aula") + '">' +
                    (aval ? "Avaliação" : "Aula") +
                '</span>' +
                '</li>';
        }
        ul.innerHTML = html;
    })();

    // ---- Precisa de atenção ----------------------------------------------
    // Três situações vigiadas, cada uma com a sua cor e ícone:
    //   aulas  -> sem aulas no cronograma      (âmbar/dourado)
    //   aval   -> sem avaliações definidas     (azul/ardósia)
    //   horas  -> horas dadas acima da previsão (vermelho)
    // Chips de filtro por tipo (com contagem) em cima; cada aviso é
    // CLICÁVEL e salta/abre o módulo respetivo na lista em baixo. Os três
    // chips aparecem sempre, mesmo a 0 — a app vigia as 3 situações e não
    // se forjam dados (um 0 é informação: "nada a assinalar aqui").
    (function atencao() {
        var ul = document.getElementById("alertasAtencao");
        var chipsBox = document.getElementById("chipsAtencao");
        if (!ul) return;

        // Metadados de cada tipo: classe de cor, ícone e rótulo do chip.
        var TIPOS = {
            aulas: { icon: "bi-calendar-x",       rotulo: "Sem aulas" },
            aval:  { icon: "bi-clipboard-x",      rotulo: "Sem avaliações" },
            horas: { icon: "bi-exclamation-octagon", rotulo: "Horas acima" }
        };
        var ORDEM = ["aulas", "aval", "horas"];

        // Construir a lista de avisos. Condições INDEPENDENTES (não else-if):
        // um módulo sem aulas E sem avaliações é duas pendências diferentes,
        // cada uma acionável por si — aparece nos dois sítios, com verdade.
        var alertas = [];
        var contagem = { aulas: 0, aval: 0, horas: 0 };
        for (var i = 0; i < mods.length; i++) {
            var m = mods[i];
            if ((m.n_aulas || 0) === 0) {
                alertas.push({ modulo: m.nome, tipo: "aulas",
                               texto: "Sem aulas marcadas no cronograma" });
                contagem.aulas++;
            }
            if ((m.n_avaliacoes || 0) === 0) {
                alertas.push({ modulo: m.nome, tipo: "aval",
                               texto: "Sem avaliações definidas" });
                contagem.aval++;
            }
            if ((m.totais || 0) > 0 && (m.dadas || 0) > (m.totais || 0)) {
                alertas.push({ modulo: m.nome, tipo: "horas",
                               texto: "Horas dadas acima das previstas" });
                contagem.horas++;
            }
        }
        var total = alertas.length;

        // Saltar para o módulo: abre o <details> e faz scroll até ele, com
        // um realce breve. O módulo é encontrado pelo data-mod-nome (evita
        // problemas de "slug" com acentos/espaços no id).
        function saltarPara(nome) {
            var alvo = null;
            var cand = document.querySelectorAll(".mod-detalhe[data-mod-nome]");
            for (var i = 0; i < cand.length; i++) {
                if (cand[i].getAttribute("data-mod-nome") === nome) { alvo = cand[i]; break; }
            }
            if (!alvo) return;
            if (alvo.tagName.toLowerCase() === "details") alvo.open = true;
            alvo.scrollIntoView({ behavior: "smooth", block: "center" });
            alvo.classList.remove("realce");
            void alvo.offsetWidth;           // reinicia a animação se repetirmos
            alvo.classList.add("realce");
        }

        var filtro = "todos";

        function desenharLista() {
            if (!total) {
                ul.innerHTML = '<li class="app-tudo-ok">' +
                    '<i class="bi bi-check-circle me-2"></i>Está tudo em dia.</li>';
                return;
            }
            var html = "";
            for (var k = 0; k < alertas.length; k++) {
                var a = alertas[k];
                if (filtro !== "todos" && a.tipo !== filtro) continue;
                html +=
                    '<li class="t-' + a.tipo + '" tabindex="0" role="button" ' +
                        'data-ir="' + escapar(a.modulo) + '" ' +
                        'title="Abrir o módulo ' + escapar(a.modulo) + '">' +
                    '<i class="bi ' + TIPOS[a.tipo].icon + '"></i>' +
                    '<span><strong>' + escapar(a.modulo) + '</strong>' +
                    '<span class="sub">' + escapar(a.texto) + '</span></span>' +
                    '</li>';
            }
            if (html === "") {
                html = '<li class="app-vazio">Sem avisos deste tipo.</li>';
            }
            ul.innerHTML = html;
        }

        function desenharChips() {
            if (!chipsBox) return;
            var html =
                '<button type="button" class="app-chip t-todos" data-filtro="todos" ' +
                    'aria-pressed="true">Todos <span class="cnt">' + total + '</span></button>';
            for (var j = 0; j < ORDEM.length; j++) {
                var t = ORDEM[j];
                html +=
                    '<button type="button" class="app-chip t-' + t + '" data-filtro="' + t + '" ' +
                        'aria-pressed="false"><span class="ponto"></span>' +
                        TIPOS[t].rotulo + ' <span class="cnt">' + contagem[t] + '</span></button>';
            }
            chipsBox.innerHTML = html;
        }

        desenharChips();
        desenharLista();

        // Clicar num chip -> muda o filtro (e o estado aria-pressed).
        if (chipsBox) {
            chipsBox.addEventListener("click", function (ev) {
                var b = ev.target.closest(".app-chip");
                if (!b) return;
                filtro = b.getAttribute("data-filtro");
                var todos = chipsBox.querySelectorAll(".app-chip");
                for (var i = 0; i < todos.length; i++) {
                    todos[i].setAttribute("aria-pressed",
                        todos[i] === b ? "true" : "false");
                }
                desenharLista();
            });
        }

        // Clicar (ou Enter/Espaço) num aviso -> salta para o módulo.
        ul.addEventListener("click", function (ev) {
            var li = ev.target.closest("li[data-ir]");
            if (li) saltarPara(li.getAttribute("data-ir"));
        });
        ul.addEventListener("keydown", function (ev) {
            if (ev.key !== "Enter" && ev.key !== " ") return;
            var li = ev.target.closest("li[data-ir]");
            if (li) { ev.preventDefault(); saltarPara(li.getAttribute("data-ir")); }
        });
    })();

    // ---- Gráficos (só se o Chart.js carregou e há módulos) ---------------
    if (typeof Chart === "undefined" || !mods.length) return;

    Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', sans-serif";
    Chart.defaults.color = "#52514e";

    // Progresso por módulo — barras horizontais, série única (verde FORAVE).
    (function progresso() {
        var cv = document.getElementById("chartProgresso");
        if (!cv) return;

        var labels = [], valores = [], detalhe = [];
        for (var i = 0; i < mods.length; i++) {
            labels.push(mods[i].nome);
            valores.push(mods[i].pct);
            detalhe.push(mods[i]);
        }

        new Chart(cv, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: valores,
                    backgroundColor: VERDE_FORAVE,
                    borderRadius: 4,
                    borderSkipped: false,
                    barThickness: 18,
                    maxBarThickness: 26
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                layout: { padding: { right: 8 } },
                scales: {
                    x: { min: 0, max: 100,
                         ticks: { callback: function (v) { return v + "%"; } },
                         grid: { color: "#e1e0d9" } },
                    y: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: function (c) {
                        var m = detalhe[c.dataIndex];
                        return m.dadas + "h de " + m.totais + "h  (" + m.pct + "%)";
                    } } }
                }
            }
        });
    })();

    // Estado dos módulos — donut semântico (concluído / em curso / planeado).
    (function estados() {
        var cv = document.getElementById("chartEstados");
        if (!cv) return;

        var contagem = { "concluido": 0, "em curso": 0, "planeado": 0 };
        for (var i = 0; i < mods.length; i++) {
            contagem[normalizarEstado(mods[i].estado)]++;
        }

        var labels = [], valores = [], cores = [];
        for (var j = 0; j < ORDEM_ESTADOS.length; j++) {
            var chave = ORDEM_ESTADOS[j];
            if (contagem[chave] > 0) {
                labels.push(ESTADOS[chave].rotulo);
                valores.push(contagem[chave]);
                cores.push(ESTADOS[chave].cor);
            }
        }

        new Chart(cv, {
            type: "doughnut",
            data: { labels: labels,
                    datasets: [{ data: valores, backgroundColor: cores,
                                 borderColor: "#fff", borderWidth: 2 }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "62%",
                plugins: {
                    legend: { position: "right",
                              labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
                    tooltip: { callbacks: { label: function (c) {
                        return c.label + ": " + c.parsed + " módulo" + (c.parsed === 1 ? "" : "s");
                    } } }
                }
            }
        });
    })();
})();
