from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from .models import Cliente
from .forms import ClienteForm
from clientes.models import Servico, Orcamento, OrcamentoItem, Venda
from django.contrib.auth.mixins import LoginRequiredMixin 
from accounts.mixins import PerfilRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from enderecos.services.cnpj_service import buscar_cnpj
from django.shortcuts import redirect, get_object_or_404
from decimal import Decimal


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

        acao = request.POST.get('acao')

        # =========================
        # DESCONTO GERAL DO ORÇAMENTO
        # =========================
        if acao == 'desconto_geral':
            desconto_tipo = request.POST.get('desconto_tipo') or None
            desconto_valor = request.POST.get('desconto_valor') or '0'

            try:
                desconto_valor = Decimal(desconto_valor)
            except:
                desconto_valor = Decimal('0.00')

            self.object.desconto_tipo = desconto_tipo
            self.object.desconto_valor = desconto_valor
            self.object.save()

            return redirect(
                'clientes:orcamento_detail',
                pk=self.object.pk
            )
        
        # =========================
        # SALVAR PROPOSTA DE PAGAMENTO (ORÇAMENTO)
        # =========================
        if acao == 'salvar_pagamento':
            self.object.tipo_pagamento = request.POST.get('tipo_pagamento') or None
            self.object.condicoes_pagamento = request.POST.get('condicoes_pagamento') or None
            self.object.observacoes_pagamento = request.POST.get('observacoes_pagamento') or None

            self.object.save()

            return redirect(
                'clientes:orcamento_detail',
                pk=self.object.pk
            )
       
        
        # =========================
        # SALVAR ORÇAMENTO (FINALIZAR)
        # =========================
        if acao == 'salvar_orcamento':
            # aqui você pode evoluir depois (ex: status = enviado)
            self.object.status = 'rascunho'
            self.object.save()

            return redirect('clientes:orcamento_list')

        # =========================
        # APROVAR ORÇAMENTO → GERAR VENDA
        # =========================
        if acao == 'aprovar_orcamento':

            # evita gerar venda duplicada
            if hasattr(self.object, 'venda'):
                return redirect('clientes:orcamento_detail', pk=self.object.pk)

            # cria a venda
            Venda.objects.create(
                empresa=self.object.empresa,
                cliente=self.object.cliente,
                orcamento=self.object,
                valor_total=self.object.total_com_desconto(),
            
            # Cópia da proposta de pagamento
            tipo_pagamento = self.object.tipo_pagamento,
            condicoes_pagamento = self.object.condicoes_pagamento,
            observacoes_pagamento = self.object.observacoes_pagamento,
            
            )
            
            # atualiza status do orçamento
            self.object.status = 'aprovado'
            self.object.save()

            return redirect('clientes:venda_list')

        # =========================
        # ADICIONAR ITEM AO ORÇAMENTO
        # =========================
        servico_id = request.POST.get('servico')
        if not servico_id:
            return redirect(
                'clientes:orcamento_detail',
                pk=self.object.pk
            )

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

        return redirect(
            'clientes:orcamento_detail',
            pk=self.object.pk
        )


@login_required
def gerar_codigo_servico(request):
    empresa = request.user.perfil.empresa
    servico = Servico(empresa=empresa)
    codigo = servico.gerar_codigo_interno()
    return JsonResponse({'codigo': codigo})


class OrcamentoListView(LoginRequiredMixin, ListView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return Orcamento.objects.filter(
            empresa=self.request.user.perfil.empresa
        )

    def post(self, request, *args, **kwargs):
        orcamento_id = request.POST.get('orcamento_id')
        novo_status = request.POST.get('status')

        if not orcamento_id or not novo_status:
            return redirect('clientes:orcamento_list')

        orcamento = get_object_or_404(
            Orcamento,
            pk=orcamento_id,
            empresa=request.user.perfil.empresa
        )

        # =========================
        # MUDANÇA DE STATUS
        # =========================
        if novo_status != orcamento.status:
            orcamento.status = novo_status
            orcamento.save()

            # =========================
            # SE APROVADO → GERAR VENDA
            # =========================
            if novo_status == 'aprovado':
                if not hasattr(orcamento, 'venda'):
                    Venda.objects.create(
                        empresa=orcamento.empresa,
                        cliente=orcamento.cliente,
                        orcamento=orcamento,
                        valor_total=orcamento.total_com_desconto(),

                        # copia proposta de pagamento
                        tipo_pagamento=orcamento.tipo_pagamento,
                        condicoes_pagamento=orcamento.condicoes_pagamento,
                        observacoes_pagamento=orcamento.observacoes_pagamento,
                    )

        return redirect('clientes:orcamento_list')


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
        return Orcamento.objects.filter(empresa=self.request.user.perfil.empresa)


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


###### VENDAS ######
class VendaListView(LoginRequiredMixin, ListView):
    model = Venda 
    template_name = 'vendas/venda_list.html'
    context_object_name = 'vendas'
    
    def get_queryset(self):
        return Venda.objects.filter(
            empresa = self.request.user.perfil.empresa
        ).select_related('cliente', 'orcamento')


class VendaDetailVew(LoginRequiredMixin, DetailView):
    model = Venda
    template_name = 'vendas/venda_detail.html'
    context_object_name = 'venda'
    
    def get_queryset(self):
        return Venda.objects.filter(
            empresa = self.request.user.perfil.empresa
        ).select_related('cliente', 'orcamento')
