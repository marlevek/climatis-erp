from django.contrib import admin
from .models import Empresa 


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'ativo', 'criado_em')
    search_fields = ('nome', 'nome_fantasia', 'cnpj')

