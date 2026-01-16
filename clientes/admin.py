from django.contrib import admin
from .models import Cliente, Fornecedor, Servico, Orcamento, OrcamentoItem


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