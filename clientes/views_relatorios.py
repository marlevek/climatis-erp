from django.shortcuts import render
from django.utils.timezone import now

from clientes.models import Parcelamento
from clientes.relatorios import (
    parcelas_em_atraso,
    resumo_inadimplencia,
)

def relatorio_inadimplencia(request):
    '''
    Tela de relatório de inadimplência:
    - lista de parcelas vencidas
    - resumo financeiro no topo
    '''
    
    parcelas = (
        parcelas_em_atraso().select_related(
            'venda',
            'venda__cliente'
        ).order_by('data_vencimento')
    )
    
    resumo = resumo_inadimplencia()
    
    context = {
        'parcelas': parcelas,
        'resumo': resumo,
        'hoje': now().date(),
    }
    
    return render(
        request, 
        'clientes/relatorios/inadimplencia.html',
        context
    )