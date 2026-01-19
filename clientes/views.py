from django.urls import reverse_lazy
import json
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Cliente
from .forms import ClienteForm
from clientes.models import Servico, Orcamento, OrcamentoItem, Venda, Parcelamento
from django.contrib.auth.mixins import LoginRequiredMixin 
from accounts.mixins import PerfilRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from enderecos.services.cnpj_service import buscar_cnpj
from django.shortcuts import redirect, get_object_or_404
from decimal import Decimal
from datetime import timedelta, datetime
from django.utils import timezone
from django.db import models
from django.db.models import Sum



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
        # DESCONTO GERAL
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

            return redirect('clientes:orcamento_detail', pk=self.object.pk)

        # =========================
        # SALVAR ORÇAMENTO (GERAL)
        # =========================
        elif acao == 'salvar_orcamento':
            self.object.tipo_pagamento = request.POST.get('tipo_pagamento') or None
            self.object.condicoes_pagamento = request.POST.get('condicoes_pagamento') or None
            self.object.observacoes_pagamento = request.POST.get('observacoes_pagamento') or None

            self.object.status = 'rascunho'
            self.object.save()

            return redirect('clientes:orcamento_list')

        # =========================
        # ADICIONAR ITEM
        # =========================
        elif acao == 'adicionar_item':
            servico_id = request.POST.get('servico')
            if not servico_id:
                return redirect('clientes:orcamento_detail', pk=self.object.pk)

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

        # =========================
        # FALLBACK DE SEGURANÇA
        # =========================
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

    def form_valid(self, form):
        orcamento = form.save(commit=False)
        orcamento.empresa = self.request.user.perfil.empresa
        orcamento.save()
        
        return redirect(
            'clientes:orcamento_detail',
            pk=orcamento.pk
        )


class OrcamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Orcamento
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



class VendaDetailView(LoginRequiredMixin, DetailView):
    model = Venda
    template_name = 'vendas/venda_detail.html'
    context_object_name = 'venda'
    
    def get_queryset(self):
        """Filtra apenas vendas da empresa do usuário"""
        return Venda.objects.filter(
            empresa=self.request.user.perfil.empresa
        ).select_related('cliente', 'orcamento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda = self.object
        
        # Buscar parcelas
        parcelas = venda.parcelas.all().order_by('numero')
        
        print(f'\n🔍 ===== GET CONTEXT DATA =====')
        print(f'🔍 Venda ID: {venda.id}')
        print(f'🔍 Tipo pagamento real: {venda.tipo_pagamento_real}')
        print(f'🔍 Forma pagamento: {venda.forma_pagamento}')
        print(f'🔍 Total parcelas: {parcelas.count()}')
        if parcelas.exists():
            for p in parcelas:
                print(f'   - Parcela #{p.numero}: R$ {p.valor} - {p.data_vencimento} - {p.forma_pagamento}')
        print(f'🔍 ==============================\n')

        context['parcelas'] = parcelas
        context['pagamento_existe'] = parcelas.exists()
        context['qtd_parcelas'] = parcelas.count()
        context['valor_total_parcelas'] = (
            parcelas.aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        return context
    
    def post(self, request, *args, **kwargs):
        """Processa o salvamento do pagamento"""
        venda = self.get_object()
        
        print(f'\n🔥 ===== POST RECEBIDO =====')
        print(f'🔥 Venda ID: {venda.id}')
        
        parcelas_json = request.POST.get('parcelas_json', '').strip()
        
        # Salvar dados principais
        venda.tipo_pagamento_real = request.POST.get('tipo_pagamento_real')
        venda.forma_pagamento = request.POST.get('forma_pagamento')
        
        # 🔥 Salvar data_pagamento se existir
        data_pagamento = request.POST.get('data_pagamento')
        if data_pagamento:
            venda.data_pagamento = data_pagamento
        
        # 🔥 Salvar valor_pagamento
        valor_pagamento = request.POST.get('valor_pagamento')
        if valor_pagamento:
            venda.valor_pagamento = Decimal(valor_pagamento)
        
        venda.observacoes_pagamento_real = request.POST.get('observacoes_pagamento')
        venda.save()
        
        print(f'🔥 Tipo pagamento: {venda.tipo_pagamento_real}')
        print(f'🔥 Forma pagamento: {venda.forma_pagamento}')
        print(f'🔥 Data pagamento: {venda.data_pagamento}')
        print(f'🔥 Valor pagamento: {venda.valor_pagamento}')

        # Processar parcelas
        if parcelas_json:
            print(f'🔥 JSON recebido (primeiros 200 chars): {parcelas_json[:200]}')
            
            # Deletar parcelas antigas
            qtd_antigas = venda.parcelas.count()
            venda.parcelas.all().delete()
            print(f'🔥 Deletadas {qtd_antigas} parcelas antigas')

            try:
                parcelas = json.loads(parcelas_json)
                print(f'🔥 Criando {len(parcelas)} novas parcelas...')
                
                for p in parcelas:
                    parcela = Parcelamento.objects.create(
                        venda=venda,
                        numero=int(p['numero']),
                        valor=Decimal(str(p['valor']).replace(',', '.')),
                        data_vencimento=p['data'],
                        forma_pagamento=p.get('forma_pagamento', ''),
                        observacao=p.get('observacao', ''),
                        status='pendente'
                    )
                    print(f'   ✅ Parcela #{parcela.numero}: R$ {parcela.valor} - {parcela.data_vencimento} - {parcela.forma_pagamento}')
                
                # Confirmar salvamento
                total_agora = venda.parcelas.count()
                print(f'🔥 Total de parcelas salvas: {total_agora}')
                
            except json.JSONDecodeError as e:
                print(f'❌ ERRO ao parsear JSON: {e}')
            except Exception as e:
                print(f'❌ ERRO ao criar parcelas: {e}')
        else:
            print(f'🔥 Nenhuma parcela enviada (JSON vazio)')
        
        print(f'🔥 ==========================\n')

        # Redireciona de volta para a mesma página
        return redirect('clientes:venda_list')