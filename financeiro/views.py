from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required 
from financeiro.forms  import LancamentoFinanceiroForm


@login_required
def novo_lancamento_financeiro(request):
    if request.method == 'POST':
        form = LancamentoFinanceiroForm(request.POST)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.origem = 'Manual'
            lancamento.save()
            return redirect('clientes:dashboard_financeiro')
    else:
        form = LancamentoFinanceiroForm()

    return render(
        request,
        'financeiro/novo_lancamento.html',
        {'form': form}
    )