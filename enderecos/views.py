from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .models import Endereco
from .forms import EnderecoForm
from accounts.mixins import PerfilRequiredMixin
from clientes.models import Cliente


class EnderecoCreateView(LoginRequiredMixin, PerfilRequiredMixin, CreateView):
    model = Endereco
    form_class = EnderecoForm
    template_name = 'enderecos/endereco_form.html'

    def get_success_url(self):
        # após salvar o endereço, volta para a lista de clientes
        return reverse_lazy('clientes:lista')

    def form_valid(self, form):
        """
        Vincula o endereço ao cliente informado na URL (?cliente=ID)
        """
        cliente_id = self.request.GET.get('cliente')
        cliente = Cliente.objects.get(
            id=cliente_id,
            empresa=self.request.user.perfil.empresa
        )
        form.instance.cliente = cliente
        return super().form_valid(form)


class EnderecoListView(LoginRequiredMixin, PerfilRequiredMixin, ListView):
    model = Endereco
    template_name = 'enderecos/endereco_list.html'
    context_object_name = 'enderecos'
    
    
    def get_queryset(self):
       cliente_id = self.request.GET.get('cliente')
       return Endereco.objects.filter(
           cliente__id = cliente_id,
           cliente__empresa = self.request.user.perfil.empresa
       ).order_by('-criado_em')
       
       
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cliente_id'] = self.request.GET.get('cliente')
        return context 
    
    

