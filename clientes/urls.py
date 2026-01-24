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
    OrcamentoDeleteView,
    OrcamentoItemUpdateView,
    OrcamentoPrintView,
    OrcamentoItemDeleteView,
    VendaListView,
    VendaDetailView,
)
from clientes.views_relatorios import relatorio_inadimplencia
from clientes.views import gerar_codigo_servico, dashboard_financeiro_view, aging_detalhe_view,  exportar_dashboard_excel, exportar_dashboard_pdf, cobrar_parcela_whatsapp
from financeiro.views import novo_lancamento_financeiro


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
    path('orcamentos/<int:pk>/excluir/', OrcamentoDeleteView.as_view(), name='orcamento_delete'),
    path('orcamenots/item/<int:pk>/excluir/', OrcamentoItemDeleteView.as_view(), name='orcamento_item_delete'),
    path('orcamentos/item/<int:pk>/editar', OrcamentoItemUpdateView.as_view(), name='orcamento_item_edit'),
    path('orcamentos/<int:pk>/imprimir/', OrcamentoPrintView.as_view(), name='orcamento_print'),

    # Vendas
    path('vendas/', VendaListView.as_view(), name='venda_list'),
    path('vendas/<int:pk>/', VendaDetailView.as_view(), name='venda_detail'),

    # Relatório Inadimplência
    path('relatorios/inadimplencia/',relatorio_inadimplencia,  name='relatorio_inadimplencia'),
    
    # Financeiro
    path("dashboard/financeiro/",dashboard_financeiro_view,        name="dashboard_financeiro"),
    path("dashboard/financeiro/aging/<str:faixa>/",
        aging_detalhe_view, name="aging_detalhe"),
    path('dashboard/financeiro/exportar/excel', exportar_dashboard_excel, name='exportar_dashboard_excel'),
    path('dashboard/financeiro/exportar/pdf', exportar_dashboard_pdf, name='exportar_dashboard_pdf'),
    path(
    "parcelamento/<int:parcela_id>/whatsapp/",
    cobrar_parcela_whatsapp,
    name="cobrar_parcela_whatsapp"),

    path('financeiro/novo/', novo_lancamento_financeiro, name='novo_lancamento_financeiro'),


]