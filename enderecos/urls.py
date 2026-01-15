from django.urls import path 
from .views import EnderecoCreateView, EnderecoListView


app_name = 'enderecos'

urlpatterns = [
    path('', EnderecoListView.as_view(), name='lista'),
    path('novo/', EnderecoCreateView.as_view(), name='novo'),
    
]