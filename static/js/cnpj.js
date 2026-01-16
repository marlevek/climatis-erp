document.addEventListener('DOMContentLoaded', function () {
    const btnBuscar = document.getElementById('buscar-cnpj');

    if (!btnBuscar) {
        console.warn('Botão buscar-cnpj não encontrado');
        return;
    }

    btnBuscar.addEventListener('click', function (event) {
        event.preventDefault();

        const cnpjInput = document.getElementById('id_documento');
        if (!cnpjInput) {
            alert('Campo de CNPJ não encontrado');
            return;
        }

        const cnpj = cnpjInput.value.replace(/\D/g, '');

        if (cnpj.length !== 14) {
            alert('CNPJ inválido');
            return;
        }

        fetch(`/clientes/buscar-cnpj/?cnpj=${cnpj}`)
            .then(response => response.json())
            .then(resp => {
                if (!resp.success) {
                    alert(resp.erro || 'Erro ao buscar CNPJ');
                    return;
                }

                const data = resp.data;

                // Cliente
                if (data.razao_social) {
                    document.getElementById('id_nome').value = data.razao_social;
                }
                if (data.nome_fantasia) {
                    document.getElementById('id_nome_fantasia').value = data.nome_fantasia;
                }
                if (data.email) {
                    document.getElementById('id_email').value = data.email;
                }
                if (data.telefone) {
                    document.getElementById('id_telefone').value = data.telefone;
                }

                // Endereço (se existir na tela)
                if (data.endereco) {
                    const map = {
                        'id_cep': data.endereco.cep,
                        'id_logradouro': data.endereco.logradouro,
                        'id_numero': data.endereco.numero,
                        'id_complemento': data.endereco.complemento,
                        'id_bairro': data.endereco.bairro,
                        'id_cidade': data.endereco.cidade,
                        'id_estado': data.endereco.estado
                    };

                    Object.keys(map).forEach(id => {
                        const el = document.getElementById(id);
                        if (el && map[id]) {
                            el.value = map[id];
                        }
                    });
                }
            })
            .catch(err => {
                console.error('Erro JS:', err);
                alert('Erro inesperado ao buscar CNPJ');
            });
    });
});
