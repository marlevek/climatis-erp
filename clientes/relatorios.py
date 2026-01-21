from django.utils.timezone import now
from django.db.models import Sum
from collections import defaultdict
from clientes.models import Parcelamento, Venda


def parcelas_em_atraso():
    return Parcelamento.objects.filter(
        status = 'pendente',
        data_vencimento__lt = now().date()
    )

def resumo_inadimplencia():
    parcelas = parcelas_em_atraso()
    
    return {
        'quantidade_parcelas': parcelas.count(),
        'valor_total': parcelas.aggregate(total=Sum('valor'))['total'] or 0
    }
    
def inadimplencia_por_aging():
    resultado = defaultdict(lambda: {
        'quantidade': 0,
        'valor_total': 0
    })

    for parcela in parcelas_em_atraso():
        faixa = parcela.faixa_aging()
        if not faixa or faixa == '-':
            continue

        resultado[faixa]['quantidade'] += 1
        resultado[faixa]['valor_total'] += parcela.valor

    return resultado


def total_em_atraso():
    '''
    Soma do valor total das parcelas vencidas e pendentes
    '''
    
    return (
        Parcelamento.objects.filter(
            status = 'pendente', data_vencimento__lt = now().date()
        ).aggregate(total=Sum('valor'))['total'] or 0
    )
    

def total_a_receber():
    """
    Soma do valor das parcelas pendentes ainda não vencidas.
    """
    return (
        Parcelamento.objects.filter(
            status ='pendente', data_vencimento__gte = now().date()
        ).aggregate(total=Sum('valor'))['total'] or 0
    )
    

def total_faturado():
      """
      Soma do valor das vendas quitadas.
      """
      return (
        Venda.objects.filter(status_financeiro='quitada')
        .aggregate(total=Sum('valor_total'))['total'] or 0
    )


def qtd_vendas_em_atraso():
    """
    Quantidade de vendas com status financeiro 'em_atraso'.
    """
    return Venda.objects.filter(status_financeiro='em_atraso').count()


def aging_dashboard():
    """
    Retorna valores por faixa de aging para o dashboard.
    """
    from collections import defaultdict

    resultado = defaultdict(lambda: 0)

    parcelas = Parcelamento.objects.filter(
        status='pendente',
        data_vencimento__lt=now().date()
    )

    for parcela in parcelas:
        faixa = parcela.faixa_aging()
        if faixa and faixa != '-':
            resultado[faixa] += parcela.valor

    return resultado
