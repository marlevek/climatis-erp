from django.urls import path
from .views import (
    ClienteListView,
    ClienteCreateView,
    ClienteUpdateView,
    BuscarCNPJView,
    ServicoListView,
    ServicoCreateView,
    ServicoUpdateView,
    OrcamentoListView,
    OrcamentoCreateView,
    OrcamentoDetailView,

)

from clientes.views import gerar_codigo_servico


app_name = 'clientes'

urlpatterns = [
    path('', ClienteListView.as_view(), name='lista'),
    path('novo/', ClienteCreateView.as_view(), name='novo'),
    path('<int:pk>/editar/', ClienteUpdateView.as_view(), name='editar'),
    path('buscar-cnpj/', BuscarCNPJView.as_view(), name='buscar_cnpj'),

    # Serviços
    path('servicos/', ServicoListView.as_view(), name='servico_list'),
    path('servicos/novo/', ServicoCreateView.as_view(), name='servico_create'),
    path('servicos/<int:pk>/editar/',
         ServicoUpdateView.as_view(), name='servico_update'),
    path('servicos/gerar-codigo/', gerar_codigo_servico,
         name='servico_gerar_codigo'),

    # Orçamentos
    path('orcamentos/', OrcamentoListView.as_view(), name='orcamento_list'),
    path('orcamentos/novo/', OrcamentoCreateView.as_view(), name='orcamento_create'),
    path('orcamentos/<int:pk>/', OrcamentoDetailView.as_view(), name='orcamento_detail'),

]
