from django.contrib import admin
from .models import Cliente, Fornecedor, Servico, Orcamento, OrcamentoItem, Venda, Parcelamento


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'tipo_pessoa', 'ativo')
    list_filter = ('tipo_pessoa', 'ativo')
    search_fields = ('nome', 'nome_fantasia', 'documento')


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'tipo_pessoa', 'ativo')
    search_fields = ('nome', 'documento')


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'codigo_interno',
        'valor_venda',
        'ativo',
    )
    search_fields = ('nome', 'codigo_interno')
    list_filter = ('ativo', )


class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'status', 'data')
    inlines = [OrcamentoItemInline]


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'empresa',
        'valor_total',
        'tipo_pagamento_real',
        'status',
        'criado_em',
    )


@admin.register(Parcelamento)
class ParcelamentoAdmin(admin.ModelAdmin):
    list_display = (
        'venda',
        'numero',
        'valor',
        'data_vencimento',
        'status',
    )
