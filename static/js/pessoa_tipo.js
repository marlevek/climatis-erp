document.addEventListener('DOMContentLoaded', function () {
    const tipoPessoa = document.getElementById('id_tipo_pessoa');
    const labelDocumento = document.getElementById('label-documento');
    const btnBuscarCnpj = document.getElementById('buscar-cnpj');

    if (!tipoPessoa || !labelDocumento) return;

    function atualizarDocumento() {
        if (tipoPessoa.value === 'PF') {
            labelDocumento.textContent = 'CPF';
            if (btnBuscarCnpj) btnBuscarCnpj.style.display = 'none';
        } else if (tipoPessoa.value === 'PJ') {
            labelDocumento.textContent = 'CNPJ';
            if (btnBuscarCnpj) btnBuscarCnpj.style.display = 'inline-block';
        } else {
            labelDocumento.textContent = 'Documento';
            if (btnBuscarCnpj) btnBuscarCnpj.style.display = 'none';
        }
    }

    // Atualiza ao carregar a página
    atualizarDocumento();

    // Atualiza ao trocar PF / PJ
    tipoPessoa.addEventListener('change', atualizarDocumento);
});
