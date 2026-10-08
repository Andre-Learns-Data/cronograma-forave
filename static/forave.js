// ============================================================
// forave.js — Comportamentos de interface partilhados
// ============================================================
// Pequenos melhoramentos de usabilidade usados em várias páginas.
// Centralizados aqui (em vez de repetidos em cada template) — é o
// mesmo princípio do forave.css para o CSS.
// ============================================================

// Mostrar/ocultar a password (evita erros de escrita silenciosos).
// Chamada pelos botões de "olho" nos campos de password.
function alternarPassword(id, botao) {
    const campo = document.getElementById(id);
    if (!campo) return;
    const icone = botao.querySelector('i');
    const mostrar = campo.type === 'password';
    campo.type = mostrar ? 'text' : 'password';
    if (icone) icone.className = mostrar ? 'bi bi-eye-slash' : 'bi bi-eye';
}

// Anti-duplo-submit: ao submeter um formulário, desativa o botão e mostra
// um spinner. Evita, por exemplo, lançar as mesmas notas duas vezes por
// duplo-clique. Se a submissão for cancelada (validação HTML5 falha, ou um
// confirm() devolve "cancelar"), o evento não chega aqui ou vem já
// "defaultPrevented" — e não mexemos no botão.
document.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;
    const form = e.target;
    if (!form || form.tagName !== 'FORM') return;

    const botao = form.querySelector('button[type="submit"], button:not([type])');
    if (!botao || botao.dataset.aSubmeter) return;

    botao.dataset.aSubmeter = '1';
    const original = botao.innerHTML;
    botao.disabled = true;
    botao.innerHTML =
        '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>A processar…';

    // Rede de segurança: se a página não navegar (ex.: erro), repõe o botão.
    setTimeout(function () {
        botao.disabled = false;
        botao.innerHTML = original;
        delete botao.dataset.aSubmeter;
    }, 4000);
});

// ------------------------------------------------------------
// Modal de confirmação reutilizável (substitui o confirm() nativo)
// ------------------------------------------------------------
// Uso: pôr data-confirmar="Mensagem?" no <form>. Ao submeter, aparece um
// diálogo com a marca em vez da caixa cinzenta do browser. Só avança quando
// o utilizador confirma. Se o Bootstrap não estiver carregado, recorre ao
// confirm() nativo (degradação graciosa).
(function () {
    var MODAL_HTML =
        '<div class="modal fade" id="modalConfirmar" tabindex="-1" aria-hidden="true">' +
        '  <div class="modal-dialog modal-dialog-centered">' +
        '    <div class="modal-content">' +
        '      <div class="modal-header">' +
        '        <h5 class="modal-title"><i class="bi bi-exclamation-triangle-fill me-2 text-warning"></i>Confirmar ação</h5>' +
        '        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>' +
        '      </div>' +
        '      <div class="modal-body" id="modalConfirmarTexto"></div>' +
        '      <div class="modal-footer">' +
        '        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>' +
        '        <button type="button" class="btn btn-danger" id="btnConfirmar"><i class="bi bi-check2 me-1"></i>Confirmar</button>' +
        '      </div>' +
        '    </div>' +
        '  </div>' +
        '</div>';

    var formPendente = null;
    var instancia = null;

    function garanteModal() {
        if (document.getElementById('modalConfirmar')) return;
        document.body.insertAdjacentHTML('beforeend', MODAL_HTML);
        document.getElementById('btnConfirmar').addEventListener('click', function () {
            if (instancia) instancia.hide();
            if (formPendente) {
                formPendente.dataset.confirmado = '1';
                formPendente.submit();  // submit() do elemento não re-dispara o evento
            }
        });
    }

    // Fase de captura: corre ANTES da guarda de anti-duplo-submit; ao parar a
    // propagação, essa guarda não desativa o botão de um form ainda por confirmar.
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (!form || form.tagName !== 'FORM') return;
        if (!form.dataset.confirmar || form.dataset.confirmado === '1') return;

        if (typeof bootstrap === 'undefined') {          // sem Bootstrap -> confirm() nativo
            if (!window.confirm(form.dataset.confirmar)) e.preventDefault();
            return;
        }

        e.preventDefault();
        e.stopPropagation();
        garanteModal();
        document.getElementById('modalConfirmarTexto').textContent = form.dataset.confirmar;
        formPendente = form;
        instancia = new bootstrap.Modal(document.getElementById('modalConfirmar'));
        instancia.show();
    }, true);
})();

// Ativa os tooltips do Bootstrap (ex.: o "i" de ajuda ao lado de um campo).
// Só corre se o Bootstrap estiver carregado na página.
document.addEventListener('DOMContentLoaded', function () {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) return;
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
});

// ------------------------------------------------------------
// PWA + estado de ligação (online/offline) + instalar como app
// ------------------------------------------------------------
// Concentrado aqui para funcionar em TODAS as páginas que carregam o
// forave.js, sem repetir código em cada template. É tudo "extra": se
// algo falhar, nunca deve partir a página (por isso os try/catch).
(function () {
    'use strict';

    // --- 1. Arrancar a PWA: garantir o <link rel="manifest"> e registar o
    // service worker. Idempotente — só injeta o manifest se ainda não existir.
    try {
        if (!document.querySelector('link[rel="manifest"]')) {
            var elo = document.createElement('link');
            elo.rel = 'manifest';
            elo.href = '/static/manifest.json';
            document.head.appendChild(elo);
        }
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function () {
                navigator.serviceWorker.register('/sw.js').catch(function () {});
            });
        }
    } catch (e) { /* a PWA é um extra — nunca deve partir a página */ }

    // --- 2. Faixa de aviso quando NÃO há ligação à internet.
    // Sem net não se alcança a base de dados partilhada, logo editar não é
    // possível. Avisamos de forma clara (em vez de falhar em silêncio) e
    // bloqueamos os botões de submeter enquanto estiver offline.
    var faixa = null;
    var botoesBloqueados = [];

    function garanteFaixa() {
        if (faixa) return faixa;
        faixa = document.createElement('div');
        faixa.id = 'avisoOffline';
        faixa.setAttribute('role', 'status');
        faixa.style.cssText =
            'position:sticky;top:0;z-index:1080;display:none;' +
            'background:#f0ad4e;color:#3d2c00;text-align:center;' +
            'padding:.5rem 1rem;font-size:.9rem;font-weight:600;' +
            'box-shadow:0 2px 6px rgba(0,0,0,.15);';
        faixa.innerHTML =
            '<i class="bi bi-wifi-off me-1"></i>' +
            'Sem ligação à internet — podes consultar, mas para guardar ' +
            'alterações precisas de estar online.';
        document.body.insertBefore(faixa, document.body.firstChild);
        return faixa;
    }

    function aplicarEstadoLigacao() {
        var offline = (navigator.onLine === false);
        garanteFaixa().style.display = offline ? 'block' : 'none';

        if (offline) {
            // Desativa os botões de submeter — não se grava sem servidor.
            // Um <button> sem type é "submit" por omissão, por isso apanhamos
            // todos os <button> que NÃO sejam type="button"/"reset", mais os
            // <input type="submit">.
            document.querySelectorAll(
                'form button:not([type="button"]):not([type="reset"]), ' +
                'form input[type="submit"]')
                .forEach(function (b) {
                    if (!b.disabled) {
                        b.disabled = true;
                        b.dataset.offlineBloqueado = '1';
                        botoesBloqueados.push(b);
                    }
                });
        } else {
            // Voltou a ligar: reativa só os que NÓS bloqueámos.
            botoesBloqueados.forEach(function (b) {
                if (b.dataset.offlineBloqueado) {
                    b.disabled = false;
                    delete b.dataset.offlineBloqueado;
                }
            });
            botoesBloqueados = [];
        }
    }

    window.addEventListener('online', aplicarEstadoLigacao);
    window.addEventListener('offline', aplicarEstadoLigacao);
    document.addEventListener('DOMContentLoaded', aplicarEstadoLigacao);

    // --- 3. Botão "Instalar aplicação" (aparece só quando é instalável).
    // O browser dispara 'beforeinstallprompt' quando a app pode ser instalada;
    // guardamos o evento e mostramos um botão flutuante que, ao ser clicado,
    // abre o instalador nativo (cria o ícone no ambiente de trabalho/telemóvel).
    var promptInstalar = null;

    function criaBotaoInstalar() {
        if (document.getElementById('btnInstalarApp')) {
            return document.getElementById('btnInstalarApp');
        }
        var btn = document.createElement('button');
        btn.id = 'btnInstalarApp';
        btn.type = 'button';
        btn.className = 'btn btn-success btn-sm shadow';
        btn.style.cssText =
            'position:fixed;right:16px;bottom:16px;z-index:1080;display:none;';
        btn.innerHTML = '<i class="bi bi-download me-1"></i>Instalar aplicação';
        btn.addEventListener('click', function () {
            if (!promptInstalar) return;
            promptInstalar.prompt();
            promptInstalar.userChoice.finally(function () {
                promptInstalar = null;
                btn.style.display = 'none';
            });
        });
        document.body.appendChild(btn);
        return btn;
    }

    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();   // evita o mini-aviso automático do browser
        promptInstalar = e;
        var btn = criaBotaoInstalar();
        if (btn) btn.style.display = 'inline-block';
    });

    window.addEventListener('appinstalled', function () {
        promptInstalar = null;
        var btn = document.getElementById('btnInstalarApp');
        if (btn) btn.style.display = 'none';
    });
})();
