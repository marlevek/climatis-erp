from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from .models import Cliente
from .forms import ClienteForm
from django.contrib.auth.mixins import LoginRequiredMixin 
from accounts.mixins import PerfilRequiredMixin
from django.http import JsonResponse
from django.views import View
from enderecos.services.cnpj_service import buscar_cnpj


class ClienteQuerysetMixin(LoginRequiredMixin, PerfilRequiredMixin):
    login_url = '/admin/login/'
    
    def get_queryset(self):
        return Cliente.objects.filter(
            empresa=self.request.user.perfil.empresa
        )


class ClienteListView(ClienteQuerysetMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'


class ClienteCreateView(LoginRequiredMixin, CreateView):
    login_url = '/admin/login/'
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        form.instance.empresa = self.request.user.perfil.empresa
        return super().form_valid(form)


class ClienteUpdateView(ClienteQuerysetMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')


class BuscarCNPJView(LoginRequiredMixin, PerfilRequiredMixin, View):
    def get(self, request):
        cnpj = request.GET.get('cnpj', '')
        dados = buscar_cnpj(cnpj)
        
        if not dados:
            return JsonResponse(
                {'success': False, 'erro': 'CNPJ inválido ou não encontrado'}, status = 200)
        
        return JsonResponse({'success': True, 'data': dados}, status=200)

