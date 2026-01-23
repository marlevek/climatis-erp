from django.utils.timezone import now
from django.db.models import Sum
from collections import defaultdict
from datetime import date 
from calendar import monthrange

from clientes.models import Parcelamento, Venda


# ===============================
# UTILITÁRIO: filtro por período
# ===============================
def aplicar_filtro_periodo(qs, mes=None, ano=None, campo_data="data"):
    if mes:
        qs = qs.filter(**{f"{campo_data}__month": mes})
    if ano:
        qs = qs.filter(**{f"{campo_data}__year": ano})
    return qs


# ===============================
# PARCELAS EM ATRASO
# ===============================
def parcelas_em_atraso(mes=None, ano=None):
    qs = Parcelamento.objects.filter(
        status="pendente",
        data_vencimento__lt=now().date()
    )
    return aplicar_filtro_periodo(qs, mes, ano, campo_data="data_vencimento")


# ===============================
# TOTAL EM ATRASO (Parcelamento)
# ===============================
def total_em_atraso(mes=None, ano=None):
    return parcelas_em_atraso(mes, ano).aggregate(
        total=Sum("valor")
    )["total"] or 0


# ===============================
# TOTAL A RECEBER (Parcelamento)
# ===============================
def total_a_receber(mes=None, ano=None):
    qs = Parcelamento.objects.filter(status="pendente")
    qs = aplicar_filtro_periodo(qs, mes, ano, campo_data="data_vencimento")

    return qs.aggregate(
        total=Sum("valor")
    )["total"] or 0


# ===============================
# TOTAL FATURADO (Venda)
# ===============================
def total_faturado(mes=None, ano=None):
    qs = Venda.objects.all()
    qs = aplicar_filtro_periodo(qs, mes, ano, campo_data="data")

    return qs.aggregate(
        total=Sum("valor_total")
    )["total"] or 0


# ===============================
# QTD VENDAS EM ATRASO
# ===============================
def qtd_vendas_em_atraso(mes=None, ano=None):
    qs = Parcelamento.objects.filter(
        status="pendente",
        data_vencimento__lt=now().date()
    )
    qs = aplicar_filtro_periodo(qs, mes, ano, campo_data="data_vencimento")

    return qs.values("venda").distinct().count()


# ===============================
# AGING DA INADIMPLÊNCIA
# ===============================
def inadimplencia_por_aging(mes=None, ano=None):
    """
    Retorna:
    {
        '0 - 30': {'quantidade': X, 'valor_total': Y},
        '31 - 60': {...},
        ...
    }
    """

    resultado = defaultdict(lambda: {
        "quantidade": 0,
        "valor_total": 0
    })

    parcelas = Parcelamento.objects.filter(
        status="pendente",
        data_vencimento__lt=now().date()
    )
    parcelas = aplicar_filtro_periodo(parcelas, mes, ano, campo_data="data_vencimento")

    for parcela in parcelas:
        faixa = parcela.faixa_aging()
        if not faixa or faixa == "-":
            continue

        resultado[faixa]["quantidade"] += 1
        resultado[faixa]["valor_total"] += parcela.valor  # <-- CORRETO

    return dict(resultado)


# ===============================
# RESUMO INADIMPLÊNCIA (LEGADO)
# ===============================
def resumo_inadimplencia(mes=None, ano=None):
    parcelas = parcelas_em_atraso(mes, ano)

    return {
        "quantidade_parcelas": parcelas.count(),
        "valor_total": parcelas.aggregate(
            total=Sum("valor")
        )["total"] or 0
    }


def calcular_mes_anterior(mes, ano):
    """
    Retorna (mes_anterior, ano_anterior)
    """
    if not mes or not ano:
        return None, None

    if mes == 1:
        return 12, ano - 1
    return mes - 1, ano


def indicador_comparativo(funcao_total, mes, ano):
    """
    Retorna:
    {
        'atual': valor_atual,
        'anterior': valor_anterior,
        'variacao': percentual ou None
    }
    """

    valor_atual = funcao_total(mes, ano)

    mes_ant, ano_ant = calcular_mes_anterior(mes, ano)
    if not mes_ant or not ano_ant:
        return {
            "atual": valor_atual,
            "anterior": None,
            "variacao": None
        }

    valor_anterior = funcao_total(mes_ant, ano_ant)

    if not valor_anterior:
        return {
            "atual": valor_atual,
            "anterior": valor_anterior,
            "variacao": None
        }

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100

    return {
        "atual": valor_atual,
        "anterior": valor_anterior,
        "variacao": round(variacao, 2)
    }