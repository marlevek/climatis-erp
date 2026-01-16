from django.urls import path 
from .views import EnderecoCreateView, EnderecoListView, EnderecoUpdateView, BuscarCEPView


app_name = 'enderecos'

urlpatterns = [
    path('', EnderecoListView.as_view(), name='lista'),
    path('novo/', EnderecoCreateView.as_view(), name='novo'),
    path('<int:pk>/editar/', EnderecoUpdateView.as_view(), name='editar'),
    path('buscar-cep/', BuscarCEPView.as_view(), name='buscar_cep'),
    
]