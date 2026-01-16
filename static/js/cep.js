document.addEventListener('DOMContentLoaded', function () {
    const btnBuscar = document.getElementById('buscar-cep');
    if (!btnBuscar) return;

    btnBuscar.addEventListener('click', function (){
        const cepInput = document.getElementById('id_cep');
        const cep = cepInput.value.replace('-', '').trim();

        if (cep.length !== 8) {
            alert('CEP inválido');
            return;
        }

        fetch(`/enderecos/buscar-cep/?cep=${cep}`)
            .then(response => response.json())
            .then(data => {
                if (data.erro) {
                    alert('CEP não encontrado');
                    return;
                }

                document.getElementById('id_logradouro').value = data.logradouro;
                document.getElementById('id_bairro').value = data.bairro;
                document.getElementById('id_cidade').value = data.cidade;
                document.getElementById('id_estado').value = data.estado;
            })
            .catch(() => alert('Erro ao buscar CEP'));

    });

});