# financeiro/services/dashboard_service.py

from django.utils.timezone import now

# ✅ Ajuste este import para onde SUAS funções estão hoje
from clientes.views import (
    financeiro_mes,
    total_a_receber,
    total_em_atraso,
    qtd_vendas_em_atraso,
    inadimplencia_por_aging,
    calcular_mes_anterior,
    indicador_comparativo,
)


def dashboard_financeiro_dados(mes=None, ano=None):
    hoje = now().date()

    dados_mes = financeiro_mes(mes, ano)

    total_faturado = dados_mes["total_faturado"]
    total_saidas = dados_mes["saidas"]
    saldo_mes = dados_mes["saldo"]

    mes_ant, ano_ant = calcular_mes_anterior(mes, ano)

    return {
        "total_faturado": total_faturado,
        "total_saidas": total_saidas,
        "saldo_mes": saldo_mes,
        "total_a_receber": total_a_receber(mes, ano),
        "total_em_atraso": total_em_atraso(mes, ano),
        "qtd_vendas_em_atraso": qtd_vendas_em_atraso(mes, ano),
        "aging": inadimplencia_por_aging(mes, ano),

        "comp_faturado": {
            "atual": total_faturado,
            "anterior": financeiro_mes(mes_ant, ano_ant)["total_faturado"] if mes_ant else None,
            "variacao": None,
        },

        "comp_em_atraso": indicador_comparativo(total_em_atraso, mes, ano),
    }
