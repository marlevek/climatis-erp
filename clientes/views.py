from django.shortcuts import get_object_or_404, redirect
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.urls import reverse_lazy
import json
import pandas as pd
from django.utils.timezone import now
from django.utils.http import urlencode
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Cliente, Empresa
from .forms import ClienteForm, OrcamentoItemForm, EmpresaForm
from clientes.models import Servico, Orcamento, OrcamentoItem, Venda, Parcelamento
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.mixins import PerfilRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from enderecos.services.cnpj_service import buscar_cnpj
from django.shortcuts import redirect, get_object_or_404
from decimal import Decimal
from datetime import timedelta, datetime
from django.utils import timezone
from django.db import models
from django.db.models import Sum
from django.shortcuts import render
from empresas.models import Empresa
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import cm
from clientes.relatorios import (
    total_em_atraso,
    total_a_receber,
    total_faturado,
    qtd_vendas_em_atraso,
    inadimplencia_por_aging,
    indicador_comparativo,
)

from clientes.relatorios import financeiro_mes, calcular_mes_anterior
from financeiro.models import LancamentoFinanceiro
from django.utils.timezone import now
from core.utils.money import parse_money, quantize_money

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
                {'success': False, 'erro': 'CNPJ inválido ou não encontrado'}, status=200)

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


# ---------- ORÇAMENTOS ------------
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
            self.object.tipo_pagamento = request.POST.get(
                'tipo_pagamento') or None
            self.object.condicoes_pagamento = request.POST.get(
                'condicoes_pagamento') or None
            self.object.observacoes_pagamento = request.POST.get(
                'observacoes_pagamento') or None

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
            desconto_percentual = request.POST.get(
                'desconto_percentual') or None
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
            # SE APROVADO → GERAR / GARANTIR VENDA
            # =========================
            if novo_status == 'aprovado':

                venda, criada = Venda.objects.get_or_create(
                    orcamento=orcamento,
                    defaults={
                        "empresa": orcamento.empresa,
                        "cliente": orcamento.cliente,
                        "valor_total": orcamento.total_com_desconto(),

                        # snapshot da proposta
                        "tipo_pagamento": orcamento.tipo_pagamento,
                        "condicoes_pagamento": orcamento.condicoes_pagamento,
                        "observacoes_pagamento": orcamento.observacoes_pagamento,
                    }
                )

                # 🔒 BLINDAGEM FINAL (ESSENCIAL)
                valor_correto = orcamento.total_com_desconto()

                if venda.valor_total != valor_correto:
                    venda.valor_total = valor_correto
                    venda.save()


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
    form_class = OrcamentoItemForm
    template_name = 'orcamentos/orcamento_item_edit.html'

    def get_success_url(self):
        return reverse_lazy(
            'clientes:orcamento_detail',
            kwargs={'pk': self.object.orcamento.id}
        )

    def get_queryset(self):
        # segurança: item só da empresa do usuário
        return OrcamentoItem.objects.filter(
            orcamento__empresa=self.request.user.perfil.empresa
        )


class OrcamentoPrintView(LoginRequiredMixin, DetailView):
    model = Orcamento
    template_name = 'orcamentos/orcamento_print.html'

# View para imprimir PDF do Orçamento
@login_required
def orcamento_pdf(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)

    empresa = orcamento.empresa
    itens = orcamento.itens.all()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="orcamento_{orcamento.id}.pdf"'
    )

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(empresa.nome, styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Orçamento Nº {orcamento.id}", styles["Heading2"]))
    elements.append(Paragraph(
        f"Data: {orcamento.data.strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Cliente: {orcamento.cliente}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    tabela = [["Serviço", "Qtde", "Valor Unit.", "Subtotal"]]

    for item in itens:
        subtotal = item.valor_unitario * item.quantidade
        tabela.append([
            item.servico.nome,
            item.quantidade,
            f"R$ {item.valor_unitario:,.2f}",
            f"R$ {subtotal:,.2f}",
        ])

    tabela.append([
        "", "", "Total",
        f"R$ {orcamento.total_com_desconto():,.2f}"
    ])

    table = Table(tabela, colWidths=[230, 60, 90, 90])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    elements.append(table)

    if orcamento.observacoes:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Observações:", styles["Heading3"]))
        elements.append(Paragraph(orcamento.observacoes, styles["Normal"]))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("__________________________________", styles["Normal"]))
    elements.append(Paragraph("Assinatura do cliente", styles["Normal"]))

    doc.build(elements)
    return response


###### VENDAS ######
class VendaListView(LoginRequiredMixin, ListView):
    model = Venda
    template_name = 'vendas/venda_list.html'
    context_object_name = 'vendas'

    def get_queryset(self):
        return Venda.objects.filter(
            empresa=self.request.user.perfil.empresa
        ).select_related('cliente', 'orcamento')



class VendaDetailView(LoginRequiredMixin, DetailView):
    model = Venda
    template_name = 'vendas/venda_detail.html'
    context_object_name = 'venda'

    def get_queryset(self):
        return Venda.objects.filter(
            empresa=self.request.user.perfil.empresa
        ).select_related('cliente', 'orcamento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venda = self.object

        parcelas = venda.parcelas.all().order_by('numero')

        context['parcelas'] = parcelas
        context['pagamento_existe'] = parcelas.exists()
        context['qtd_parcelas'] = parcelas.count()
        context['valor_total_parcelas'] = (
            parcelas.aggregate(total=Sum('valor'))['total']
            or Decimal('0.00')
        )

        # ✅ PASSO 1: enviar parcelas salvas em JSON para o template
        context['valor_pagamento'] = venda.valor_total
        
        context['parcelas_salvas_json'] = json.dumps([
            {
                "numero": p.numero,
                "valor": str(p.valor),
                "data": p.data_vencimento.strftime("%Y-%m-%d"),
                "forma_pagamento": p.forma_pagamento or "",
                "observacao": p.observacao or "",
                "status": p.status,
            }
            for p in parcelas
        ])

        return context


    def post(self, request, *args, **kwargs):
        venda = self.get_object()

        print(f'\n🔥 POST Venda #{venda.id}')

        # =========================
        # DADOS DE PAGAMENTO REAL
        # =========================
        venda.tipo_pagamento_real = request.POST.get('tipo_pagamento_real')
        venda.forma_pagamento = request.POST.get('forma_pagamento')

        data_pagamento = request.POST.get('data_pagamento')
        if data_pagamento:
            venda.data_pagamento = data_pagamento

        valor_pagamento = request.POST.get("valor_pagamento")
        venda.valor_pagamento = quantize_money(parse_money(valor_pagamento, default=None)) or Decimal("0.00")

        venda.observacoes_pagamento_real = request.POST.get('observacoes_pagamento')
        venda.save()

        # =========================
        # PARCELAS (somente se vier JSON válido)
        # =========================
        parcelas_json = request.POST.get('parcelas_json', '').strip()
        print(f'📦 parcelas_json: [{parcelas_json}]')
        
        alterou_parcelas = request.POST.get('alterou_parcelas') == '1'

        if parcelas_json and parcelas_json not in ('[]', 'null', '{}') and alterou_parcelas:

            try:
                parcelas = json.loads(parcelas_json)

                if isinstance(parcelas, list) and parcelas:
                    print('🔄 Atualizando parcelas…')

                    venda.parcelas.all().delete()

                    for p in parcelas:
                        valor = quantize_money(parse_money(p.get("valor"), default=Decimal("0.00")))
                        Parcelamento.objects.create(
                            venda=venda,
                            numero=int(p.get['numero']),
                            valor=valor,
                            #default=Decimal("0.00"),
                            data_vencimento=p.get['data'],
                            forma_pagamento=p.get('forma_pagamento', ''),
                            observacao=p.get('observacao', ''),
                            status=p.get('status', 'pendente'),
                        )

                    print(f'✅ Parcelas salvas: {venda.parcelas.count()}')
                else:
                    print('ℹ️ JSON vazio — parcelas mantidas.')

            except Exception as e:
                print(f'❌ Erro parcelas: {e}')
        else:
            print('ℹ️ Nenhuma alteração em parcelas.')

        print('🔥 POST finalizado\n')

        return redirect('clientes:venda_detail', pk=venda.pk)

from financeiro.services.dashboard_service import dashboard_financeiro_dados

# FINANCEIRO
@login_required
def dashboard_financeiro_view(request):
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    mes = int(mes) if mes else None
    ano = int(ano) if ano else None

    context = dashboard_financeiro_dados(mes, ano)
    context.update({
        "mes_selecionado": mes,
        "ano_selecionado": ano,
    })

    return render(
        request,
        "clientes/dashboard_financeiro.html",
        context
    )


@login_required
def aging_detalhe_view(request, faixa):
    """
    Lista parcelas em atraso filtradas por faixa de aging.
    Aceita mes/ano via GET para manter consistência com o dashboard.
    """
    mes_raw = request.GET.get("mes")
    ano_raw = request.GET.get("ano")

    mes = int(mes_raw) if mes_raw and mes_raw != 'None' else None
    ano = int(ano_raw) if ano_raw and ano_raw != 'None' else None

    parcelas = Parcelamento.objects.filter(
        status="pendente",
        data_vencimento__lt=now().date()
    )

    if mes:
        parcelas = parcelas.filter(data_vencimento__month=mes)
    if ano:
        parcelas = parcelas.filter(data_vencimento__year=ano)

    # filtra pela faixa usando a regra do model
    parcelas_filtradas = []

    for p in parcelas:
        if p.faixa_aging() == faixa:
            p.mensagem_whatsapp = (
                f"Olá {p.venda.cliente.nome}, "
                f"identificamos uma parcela em aberto no valor de R$ {p.valor:.2f} "
                f"com vencimento em {p.data_vencimento.strftime('%d/%m/%Y')}. "
                f"Podemos regularizar?"
            )
            parcelas_filtradas.append(p)

    parcelas = parcelas_filtradas

    # temporário para whatsapp
    telefone_cobranca = '41996131762'

    context = {
        "faixa": faixa,
        "parcelas": parcelas,
        "mes": mes,
        "ano": ano,
        'telefone_cobranca': telefone_cobranca,
    }

    return render(
        request,
        "clientes/aging_detalhe.html",
        context
    )


@login_required
def cobrar_parcela_whatsapp(request, parcela_id):
    parcela = get_object_or_404(Parcelamento, id=parcela_id)

    # marca automaticamente como enviado
    if parcela.status_cobranca != "enviado":
        parcela.status_cobranca = "enviado"
        parcela.save(update_fields=["status_cobranca"])

    telefone = request.GET.get("telefone")

    # monta a mensagem AQUI (sempre disponível)
    mensagem = (
        f"Olá {parcela.venda.cliente}, "
        f"identificamos uma parcela em aberto no valor de R$ {parcela.valor:.2f} "
        f"com vencimento em {parcela.data_vencimento.strftime('%d/%m/%Y')}. "
        f"Podemos regularizar?"
    )

    params = urlencode({"text": mensagem})

    return redirect(f"https://wa.me/55{telefone}?{params}")


# EXPORTAR DASHBOARD
@login_required
def exportar_dashboard_excel(request):
    mes_raw = request.GET.get("mes")
    ano_raw = request.GET.get("ano")

    mes = int(mes_raw) if mes_raw and mes_raw != "None" else None
    ano = int(ano_raw) if ano_raw and ano_raw != "None" else None
    
    dados = dashboard_financeiro_dados(mes, ano)
    
    from core.utils.money import excel_money
    
    # ---------- Indicadores ----------
    indicadores = {
        "Total Faturado": excel_money(dados["total_faturado"]),
        "Total de Saídas": excel_money(dados["total_saidas"]),
        "Saldo do Mês": excel_money(dados["saldo_mes"]),
        "Total a Receber": excel_money(dados["total_a_receber"]),
        "Total em Atraso": excel_money(dados["total_em_atraso"]),
        "Qtd. Vendas em Atraso": dados["qtd_vendas_em_atraso"],
    }

    df_indicadores = pd.DataFrame(
        list(indicadores.items()),
        columns=["Indicador", "Valor"]
    )

    # ---------- Aging ----------
    aging = dados['aging']
    df_aging = pd.DataFrame([
        {
            "Faixa": faixa,
            "Quantidade": dados["quantidade"],
            "Valor Total":excel_money(dados["valor_total"])
        }
        for faixa, dados in aging.items()
    ])

    # ---------- Resposta ----------
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="dashboard_financeiro.xlsx"'

    with pd.ExcelWriter(response, engine="openpyxl") as writer:

        df_indicadores.to_excel(writer, sheet_name="Indicadores", index=False)
        df_aging.to_excel(writer, sheet_name="Aging", index=False)

        workbook = writer.book

        # ---------- Indicadores ----------
        ws_ind = writer.sheets["Indicadores"]

        for row in range(2, ws_ind.max_row + 1):
            if ws_ind.cell(row=row, column=1).value != "Qtd. Vendas em Atraso":
                ws_ind.cell(row=row, column=2).number_format = 'R$ #,##0.00'

        ws_ind.column_dimensions["A"].width = 30
        ws_ind.column_dimensions["B"].width = 20

        # ---------- Aging ----------
        ws_aging = writer.sheets["Aging"]
        ws_aging.column_dimensions["A"].width = 15
        ws_aging.column_dimensions["B"].width = 15
        ws_aging.column_dimensions["C"].width = 20

        for row in range(2, ws_aging.max_row + 1):
            ws_aging.cell(row=row, column=3).number_format = 'R$ #,##0.00'

    return response


# Exportar PDF
@login_required
def exportar_dashboard_pdf(request):

    text_styles = getSampleStyleSheet()

    empresa = Empresa.objects.first()
    nome_empresa = empresa.nome if empresa else 'Nome da sua Empresa'
    logo_path = None
    if empresa and hasattr(empresa, 'logo') and empresa.logo:
        logo_path = empresa.logo.path

    mes_raw = request.GET.get("mes")
    ano_raw = request.GET.get("ano")

    mes = int(mes_raw) if mes_raw and mes_raw != "None" else None
    ano = int(ano_raw) if ano_raw and ano_raw != "None" else None

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="dashboard_financeiro.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)

    elements = []

    if logo_path:
        elements.append(
            Image(
                logo_path,
                width=4 * cm,
                height=2 * cm,
                hAlign='LEFT'
            )
        )
    elements.append(Paragraph(nome_empresa, text_styles['Title']))
    elements.append(Spacer(1, 12))

    # -------- TÍTULO --------
    elements.append(Paragraph("Dashboard Financeiro", text_styles["Title"]))
    elements.append(Spacer(1, 12))

    # -------- INDICADORES --------
    dados = dashboard_financeiro_dados(mes, ano)
    indicadores = [
        ["Indicador", "Valor (R$)"],
        ["Total Faturado", f"{dados['total_faturado']:,.2f}"],
        ["Total de Saídas", f"{dados['total_saidas']:,.2f}"],
        ["Saldo do Mês", f"{dados['saldo_mes']:,.2f}"],
        ["Total a Receber", f"{dados['total_a_receber']:,.2f}"],
        ["Total em Atraso", f"{dados['total_em_atraso']:,.2f}"],
        ["Qtd. Vendas em Atraso", dados["qtd_vendas_em_atraso"]],
    ]

    tabela_ind = Table(indicadores, colWidths=[250, 150])
    tabela_ind.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(tabela_ind)
    elements.append(Spacer(1, 20))

    # -------- AGING --------
    elements.append(
        Paragraph("Aging da Inadimplência", text_styles["Heading2"]))
    elements.append(Spacer(1, 10))

    aging_data = [["Faixa", "Qtd Parcelas", "Valor Total (R$)"]]
    aging = dados['aging']

    for faixa, dados in aging.items():
        aging_data.append([
            faixa,
            dados["quantidade"],
            f"{dados['valor_total']:,.2f}"
        ])

    tabela_aging = Table(aging_data, colWidths=[150, 150, 150])
    tabela_aging.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(tabela_aging)

    doc.build(elements)
    return response


# Parcelas
def parcelas_list(request):
    hoje = now().date()
    filtro = request.GET.get('status')

    parcelas = Parcelamento.objects.select_related(
        'venda',
        'venda__cliente'
    )

    if filtro == 'pendente':
        parcelas = parcelas.filter(status='pendente', data_vencimento__gte=hoje)

    elif filtro == 'paga':
        parcelas = parcelas.filter(status='paga')

    elif filtro == 'atraso':
        parcelas = parcelas.filter(status='pendente', data_vencimento__lt=hoje)

    parcelas = parcelas.order_by('data_vencimento')

    # Totais
    total_a_receber = parcelas.filter(status='pendente').aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_em_atraso = parcelas.filter(
        status='pendente',
        data_vencimento__lt=hoje
    ).aggregate(
        total=Sum('valor')
    )['total'] or 0

    return render(
        request,
        'clientes/parcelas_list.html',
        {
            'parcelas': parcelas,
            'filtro': filtro,
            'total_a_receber': total_a_receber,
            'total_em_atraso': total_em_atraso,
        }
    )


@login_required
def empresa_update_view(request):
    # por enquanto ERP monoempresa
    empresa = Empresa.objects.first()

    if request.method == "POST":
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect("clientes:empresa_update")
    else:
        form = EmpresaForm(instance=empresa)

    return render(
        request,
        "clientes/configuracoes/empresa_form.html",
        {"form": form}
    )