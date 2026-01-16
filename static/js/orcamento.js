document.addEventListener('DOMContentLoaded', function () {
  const select = document.getElementById('servico-select');
  const valorInput = document.getElementById('valor-unitario');

  if (!select || !valorInput) return;

  select.addEventListener('change', function () {
    const option = select.options[select.selectedIndex];
    const valor = option.getAttribute('data-valor');

    if (valor) {
      valorInput.value = valor;
    }
  });
});
