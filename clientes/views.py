from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from .models import Cliente
from .forms import ClienteForm
from clientes.models import Servico, Orcamento, OrcamentoItem
from django.contrib.auth.mixins import LoginRequiredMixin 
from accounts.mixins import PerfilRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from enderecos.services.cnpj_service import buscar_cnpj
from django.shortcuts import redirect


# CLIENTES
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


# Serviços
class ServicoListView(LoginRequiredMixin, ListView):
    model = Servico
    template_name = 'servicos/servico_list.html'

    def get_queryset(self):
        return Servico.objects.filter(
            empresa=self.request.user.perfil.empresa
        )


class ServicoCreateView(LoginRequiredMixin, CreateView):
    model = Servico
    fields = [
        'nome',
        'codigo_interno',
        'valor_custo',
        'valor_venda',
        'comissao_percentual',
        'descricao',
        'ativo',
    ]
    template_name = 'servicos/servico_form.html'
    success_url = '/clientes/servicos/'

    def form_valid(self, form):
        form.instance.empresa = self.request.user.perfil.empresa
        return super().form_valid(form)


class ServicoUpdateView(LoginRequiredMixin, UpdateView):
    model = Servico
    fields = ServicoCreateView.fields
    template_name = 'servicos/servico_form.html'
    success_url = '/clientes/servicos/'
    

#---------- ORÇAMENTOS ------------
class OrcamentoDetailView(LoginRequiredMixin, DetailView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_detail.html'

    def get_queryset(self):
        return Orcamento.objects.filter(
            empresa=self.request.user.perfil.empresa
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        servico_id = request.POST.get('servico')
        quantidade = int(request.POST.get('quantidade', 1))
        desconto_percentual = request.POST.get('desconto_percentual') or None
        desconto_valor = request.POST.get('desconto_valor') or None
        descricao = request.POST.get('descricao')

        servico = Servico.objects.get(
            id=servico_id,
            empresa=request.user.perfil.empresa
        )

        OrcamentoItem.objects.create(
            orcamento=self.object,
            servico=servico,
            descricao=descricao,
            quantidade=quantidade,
            valor_unitario=servico.valor_venda,
            desconto_percentual=desconto_percentual,
            desconto_valor=desconto_valor,
        )

        return redirect('clientes:orcamento_detail', pk=self.object.pk)


@login_required
def gerar_codigo_servico(request):
    empresa = request.user.perfil.empresa
    servico = Servico(empresa=empresa)
    codigo = servico.gerar_codigo_interno()
    return JsonResponse({'codigo': codigo})


class OrcamentoListView(LoginRequiredMixin, ListView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_list.html'

    def get_queryset(self):
        return Orcamento.objects.filter(
            empresa=self.request.user.perfil.empresa
        )


class OrcamentoCreateView(LoginRequiredMixin, CreateView):
    model = Orcamento
    fields = ['cliente', 'observacoes']
    template_name = 'orcamentos/orcamento_form.html'
    success_url = reverse_lazy('clientes:orcamento_list')

    def form_valid(self, form):
        form.instance.empresa = self.request.user.perfil.empresa
        return super().form_valid(form)


class OrcamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_delete.html'
    success_url = reverse_lazy('clientes:orcamento_list')

    def get_queryset(self):
        # garante que só exclui orçamento da empresa do usuário
        return Orcamento.objects.filter(empresa=self.request.user.empresa)


class OrcamentoItemDeleteView(LoginRequiredMixin, DeleteView):
    model = OrcamentoItem
    template_name = 'orcamentos/orcamento_item_delete.html'

    def get_success_url(self):
        return reverse_lazy(
            'clientes:orcamento_detail',
            kwargs={'pk': self.object.orcamento.id}
        )

    def get_queryset(self):
        return OrcamentoItem.objects.all()


class OrcamentoItemUpdateView(LoginRequiredMixin, UpdateView):
    model = OrcamentoItem
    template_name = 'orcamentos/orcamento_item_edit.html'
    fields = [
        'quantidade',
        'valor_unitario',
        'desconto_percentual',
        'desconto_valor',
        'descricao',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'clientes:orcamento_detail',
            kwargs={'pk': self.object.orcamento.id}
        )

    def get_queryset(self):
        # segurança: item só da empresa do usuário
        return OrcamentoItem.objects.all()


class OrcamentoPrintView(LoginRequiredMixin, DetailView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_print.html'

    def get_queryset(self):
        # segurança: só permite imprimir orçamento da empresa do usuário
        return Orcamento.objects.filter(
            empresa=self.request.user.empresa
        )

