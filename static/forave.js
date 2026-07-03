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
