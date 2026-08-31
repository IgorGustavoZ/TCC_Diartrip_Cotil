/**
 * Modal de confirmação genérico do DiarTrip — substitui confirm() nativo em
 * qualquer ação (destrutiva ou não) mantendo o mesmo visual em todas as páginas.
 *
 * Uso: incluir <script src="../static/confirm-modal.js"></script> (depois de
 * i18n.js) e chamar:
 *
 *   abrirModalConfirmacao({
 *       titulo, mensagem, textoConfirmar, textoCancelar,
 *       tipo: 'perigo' | 'padrao',
 *       onConfirmar: async () => { ...ação existente... }
 *   })
 *
 * O CSS (.confirm-modal-*) fica em static/style.css. O markup é injetado
 * automaticamente no <body> na primeira vez que a página carrega.
 */

let confirmModalCallback = null

function abrirModalConfirmacao({ titulo, mensagem, textoConfirmar, textoCancelar, tipo = 'padrao', onConfirmar }) {
    document.getElementById("confirmModalTitulo").textContent = titulo
    document.getElementById("confirmModalMsg").textContent = mensagem

    const btnCancelar = document.getElementById("confirmModalCancelar")
    const btnConfirmar = document.getElementById("confirmModalConfirmar")
    btnCancelar.textContent = textoCancelar || t('common.cancel')
    btnConfirmar.textContent = textoConfirmar
    btnConfirmar.disabled = false

    document.getElementById("confirmModalIcon").classList.toggle("perigo", tipo === "perigo")
    btnConfirmar.classList.toggle("perigo", tipo === "perigo")

    confirmModalCallback = onConfirmar

    const ov = document.getElementById("confirmModalOv")
    ov.classList.remove("fechando")
    ov.classList.add("ativo")
    document.addEventListener("keydown", onKeydownConfirmModal)
    setTimeout(() => btnCancelar.focus(), 0)
}

function fecharModalConfirmacao(e) {
    if (e && e.target !== e.currentTarget) return
    fecharModalConfirmacaoForcado()
}

function fecharModalConfirmacaoForcado() {
    const ov = document.getElementById("confirmModalOv")
    if (!ov.classList.contains("ativo")) return
    ov.classList.add("fechando")
    setTimeout(() => {
        ov.classList.remove("ativo", "fechando")
    }, 150)
    document.removeEventListener("keydown", onKeydownConfirmModal)
    confirmModalCallback = null
}

function onKeydownConfirmModal(e) {
    if (e.key === "Escape") fecharModalConfirmacaoForcado()
}

function _injetarModalConfirmacao() {
    if (document.getElementById("confirmModalOv")) return

    const wrapper = document.createElement("div")
    wrapper.innerHTML = `
<div class="confirm-modal-ov" id="confirmModalOv" onclick="fecharModalConfirmacao(event)">
    <div class="confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="confirmModalTitulo" aria-describedby="confirmModalMsg">
        <div class="confirm-modal-icon" id="confirmModalIcon">⚠</div>
        <h3 class="confirm-modal-titulo" id="confirmModalTitulo"></h3>
        <p class="confirm-modal-msg" id="confirmModalMsg"></p>
        <div class="confirm-modal-acoes">
            <button class="confirm-modal-btn confirm-modal-cancelar" id="confirmModalCancelar"></button>
            <button class="confirm-modal-btn confirm-modal-confirmar" id="confirmModalConfirmar"></button>
        </div>
    </div>
</div>`.trim()

    document.body.appendChild(wrapper.firstChild)

    document.getElementById("confirmModalCancelar").addEventListener("click", () => fecharModalConfirmacaoForcado())
    document.getElementById("confirmModalConfirmar").addEventListener("click", async () => {
        const callback = confirmModalCallback
        const btn = document.getElementById("confirmModalConfirmar")
        btn.disabled = true
        try {
            if (callback) await callback()
        } finally {
            btn.disabled = false
            fecharModalConfirmacaoForcado()
        }
    })
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _injetarModalConfirmacao)
} else {
    _injetarModalConfirmacao()
}
