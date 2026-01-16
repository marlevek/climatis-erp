document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('btn-gerar-codigo');
    if (!btn) return;

    btn.addEventListener('click', function () {
        fetch('/clientes/servicos/gerar-codigo/')
            .then(response => response.json())
            .then(data => {
                const input = document.getElementById('id_codigo_interno');
                if (input) input.value = data.codigo;
            })
            .catch(() => alert('Erro ao gerar código'));
    });
});
