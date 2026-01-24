from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from financeiro.forms  import LancamentoFinanceiroForm
from financeiro.models import LancamentoFinanceiro
from django.utils.timezone import now 


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


@login_required
def lista_lancamentos_financeiros(request):
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    hoje = now().date()
    mes = int(mes) if mes else hoje.month
    ano = int(ano) if ano else hoje.year

    lancamentos = LancamentoFinanceiro.objects.filter(
        data__month=mes,
        data__year=ano
    ).order_by('-data', '-id')

    context = {
        'lancamentos': lancamentos,
        'mes_selecionado': mes,
        'ano_selecionado': ano,
    }

    return render(
        request,
        'financeiro/lista_lancamentos.html',
        context
    )


@login_required
def editar_lancamento_financeiro(request, lancamento_id):
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id)

    if request.method == 'POST':
        form = LancamentoFinanceiroForm(request.POST, instance=lancamento)
        if form.is_valid():
            form.save()
            return redirect('clientes:lista_lancamentos_financeiros')
    else:
        form = LancamentoFinanceiroForm(instance=lancamento)

    return render(
        request,
        'financeiro/novo_lancamento.html',
        {'form': form}
    )


@login_required
def excluir_lancamento_financeiro(request, lancamento_id):
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id)
    lancamento.delete()
    return redirect('clientes:lista_lancamentos_financeiros')


