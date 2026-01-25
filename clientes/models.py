from django.db import models
from django.db.models import Max
from empresas.models import Empresa 
from decimal import Decimal
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from collections import defaultdict
from django.core.exceptions import ValidationError
from core.utils.money import quantize_money
import re 


def clean(self):
    super().clean()
    if self.valor is not None:
        self.valor = quantize_money(self.valor)
        

class Cliente(models.Model):
    TIPO_PESSOA_CHOICES = (
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES
    )

    nome = models.CharField(max_length=200)
    nome_fantasia = models.CharField(
        max_length=200,
        blank=True,
        help_text='Obrigatório apenas para PJ'
    )

    documento = models.CharField(
        max_length=18,
        help_text='CPF ou CNPJ'
    )

    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        unique_together = ('empresa', 'documento')

    def __str__(self):
        return self.nome_fantasia or self.nome


class Fornecedor(models.Model):
    TIPO_PESSOA_CHOICES = (
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='fornecedores'
    )

    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES
    )

    nome = models.CharField(max_length=255)
    documento = models.CharField(max_length=20)

    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, null=True)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empresa', 'documento')
        ordering = ['nome']

    def __str__(self):
        return self.nome


# SERVIÇOS
class Servico(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='servicos'
    )

    nome = models.CharField(max_length=255)
    codigo_interno = models.CharField(max_length=50)

    valor_custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    valor_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    comissao_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Percentual de comissão'
    )

    descricao = models.TextField(blank=True, null=True)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empresa', 'codigo_interno')
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    # Código interno serviço
    def gerar_codigo_interno(self):
        ultimo = (
            Servico.objects.filter(
                empresa = self.empresa,
                codigo_interno__startswith='SRV-').aggregate(max_codigo = Max('codigo_interno')).get('max_codigo')
            )
        
        if ultimo:
            numero = int(re.findall(r'\d+', ultimo)[-1]) + 1
        else:
            numero = 1
            
        return f'SRV-{numero:04d}'

    def save(self, *args, **kwargs):
        if not self.codigo_interno:
            self.codigo_interno = self.gerar_codigo_interno()
        super().save(*args, **kwargs)
        
        
# Orçamentos
class Orcamento(models.Model):
    STATUS_CHOICES = (
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    )
       
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='orcamentos'
    )
    
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='orcamentos'
    )

    data = models.DateField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rascunho'
    )
    
    observacoes = models.TextField(blank=True, null=True)
    
    TIPO_PAGAMENTOS_CHOICES = (
        ('avista', 'À vista'),
        ('parcelado', 'Parcelado'),
    )
    
    tipo_pagamento = models.CharField(
        max_length=20, 
        choices=TIPO_PAGAMENTOS_CHOICES,
        blank=True,
        null=True,
        help_text='Forma de pagamento proposta ao cliente'
    )
    
    condicoes_pagamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Ex.: 3x sem juros, Entrada + 2 parcelas'
    )
    
    observacoes_pagamento = models.TextField(
        blank=True,
        null=True,
        help_text='Ex.: 50% entrada na confirmação do serviço'
    )
    
    
    TIPO_DESCONTO_GERAL_CHOICES = (
        ('percentual', 'Percentual (%)'),
        ('valor', 'Valor (R$)'),
    )
    
    desconto_tipo = models.CharField(
        max_length=20,
        choices=TIPO_DESCONTO_GERAL_CHOICES,
        blank=True,
        null=True,
    )
    
    desconto_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )  
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data']
    
    
    def __str__(self):
        return f'Orçamento #{self.id} - {self.cliente}'
    
    
    def total_itens(self):
        total = Decimal('0.00')

        for item in self.itens.all():
            total += (item.valor_unitario or Decimal('0.00')) * (item.quantidade or 0)

        return total
        
        
    def valor_desconto_geral(self):
        """
        Calcula o desconto aplicado AO ORÇAMENTO INTEIRO.
        """
        total = self.total_itens()

        if not self.desconto_valor or self.desconto_valor <= 0:
            return Decimal('0.00')

        if self.desconto_tipo == 'percentual':
            return (total * self.desconto_valor / Decimal('100')).quantize(Decimal('0.01'))

        return min(self.desconto_valor, total)


    def total_com_desconto(self):
        """
        Total final do orçamento (itens - desconto geral).
        """
        total = self.total_itens()
        desconto = self.valor_desconto_geral()

        return max(
            (total - desconto).quantize(Decimal('0.01')),
            Decimal('0.00')
        )

        
    def total(self):
        """
        Mantido por compatibilidade com código existente.
        """
        return self.total_itens()
    
    
class OrcamentoItem(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT
    )

    descricao = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Detalhes do serviço (ex: Limpeza de 4 splits)'
    )

    quantidade = models.PositiveIntegerField(default=1)

    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    desconto_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Desconto em %'
    )

    desconto_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Desconto em valor fixo'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def subtotal_bruto(self):
        return self.quantidade * self.valor_unitario

    def valor_desconto(self):
        bruto = self.subtotal_bruto()

        if self.desconto_valor:
            return self.desconto_valor

        if self.desconto_percentual:
            return (bruto * self.desconto_percentual) / 100

        return 0

    def subtotal(self):
        return self.subtotal_bruto() - self.valor_desconto()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.orcamento.save()

    def __str__(self):
        return f'{self.servico} ({self.quantidade}x)'
    
   
########## VENDA ##########
class Venda(models.Model):
    STATUS_CHOICES = (
        ('aberta', 'Aberta'),
        ('faturada', 'Faturada'),
        ('cancelada', 'Cancelada'),
    )

    TIPO_PAGAMENTO_CHOICES = (
        ('avista', 'À vista'),
        ('parcelado', 'Parcelado'),
    )
    
    STATUS_FINANCEIRO_CHOICES = (
        ('aberta', 'Aberta'),
        ('parcial', 'Parcial'),
        ('quitada', 'Quitada'),
        ('em_atraso', 'Em atraso'),
    )
    
    status_financeiro = models.CharField(
        max_length=10,
        choices=STATUS_FINANCEIRO_CHOICES,
        default='aberta'
    )
    
    def calcular_status_financeiro(self):
        """
    Calcula o status financeiro da venda com base nas parcelas.
    Regra:
    - Aberta: nenhuma parcela paga
    - Parcial: ao menos uma paga e ainda existe parcela em aberto
    - Quitada: todas pagas
    """
        parcelas_validas = self.parcelas.exclude(status='cancelada')
        
        # se não há parcelas válidas, considera aberta
        if not parcelas_validas.exists():
            return 'aberta'
        
        total = parcelas_validas.count()
        pagas = parcelas_validas.filter(status='paga').count()
        
        if pagas == total:
           return 'quitada'
       
        if self.possui_parcelas_em_atraso():
            return 'em_atraso'
        
        if pagas > 0:
            return 'parcial'
        
        return 'aberta'
        
    def atualizar_status_financeiro(self):
        novo_status = self.calcular_status_financeiro()
        
        if self.status_financeiro != novo_status:
            type(self).objects.filter(pk=self.pk).update(
                status_financeiro=novo_status
            )
    
    def possui_parcelas_em_atraso(self):
        return self.parcelas.filter(
            status = 'pendente',
            data_vencimento__lt = now().date()
        ).exists()
        
         
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='vendas'
    )

    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='vendas'
    )

    orcamento = models.OneToOneField(
        'clientes.Orcamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='venda'
    )

    data = models.DateField(auto_now_add=True)

    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aberta'
    )

    # =========================
    # PROPOSTA (do orçamento)
    # =========================
    tipo_pagamento = models.CharField(
        max_length=20,
        choices=TIPO_PAGAMENTO_CHOICES,
        blank=True,
        null=True
    )

    condicoes_pagamento = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    observacoes_pagamento = models.TextField(
        blank=True,
        null=True
    )

    # =========================
    # PAGAMENTO REAL (financeiro)
    # =========================
    tipo_pagamento_real = models.CharField(
        max_length=20,
        choices=TIPO_PAGAMENTO_CHOICES,
        blank=True,
        null=True
    )

    forma_pagamento = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    data_pagamento = models.DateField(
        blank=True,
        null=True
    )

    valor_pagamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    observacoes_pagamento_real = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    
    def gerar_parcelas(
        self,
        qtd_parcelas,
        data_primeira,
        intervalo_dias,
        parcelas_payload=None
    ):
        """
    Gera parcelas de forma profissional.
    Se parcelas_payload não tiver valor da 1ª parcela,
    divide o valor total igualmente.
    """

        # limpeza segura
        self.parcelas.all().delete()

        valor_total = self.valor_total

        # Caso não venha payload (ex: backend puro)
        if not parcelas_payload:
            valor_parcela = (valor_total / qtd_parcelas).quantize(Decimal('0.01'))

            for i in range(qtd_parcelas):
                Parcelamento.objects.create(
                    venda=self,
                    numero=i + 1,
                    valor=valor_parcela,
                    data_vencimento=data_primeira + timedelta(days=i * intervalo_dias),
                    status='pendente'
                )
            return

        # Caso venha payload do frontend
        primeira = parcelas_payload[0]
        valor_primeira_raw = (primeira.get('valor') or '').strip()
        
        try:
            valor_primeira = Decimal(
                valor_primeira_raw.replace(',', '.')
            )
        except:
            valor_primeira = Decimal('0.00')

        # REGRA-CHAVE
        if valor_primeira_raw <= Decimal('0.00'):
            valor_parcela = (valor_total / qtd_parcelas).quantize(Decimal('0.01'))

            for i in range(qtd_parcelas):
                Parcelamento.objects.create(
                    venda=self,
                    numero=i + 1,
                    valor=valor_parcela,
                    data_vencimento=data_primeira + timedelta(days=i * intervalo_dias),
                    forma_pagamento=primeira.get('forma_pagamento'),
                    observacao=primeira.get('observacao') or '',
                    status='pendente'
                )
            return

        # Caso exista entrada
        restante = valor_total - valor_primeira
        qtd_restante = qtd_parcelas - 1

        if qtd_restante <= 0:
            return

        valor_restante = (restante / qtd_restante).quantize(Decimal('0.01'))

        for i in range(qtd_parcelas):
            if i == 0:
                valor = valor_primeira
            else:
                valor = valor_restante

            data = data_primeira + timedelta(days=i * intervalo_dias)

            Parcelamento.objects.create(
                venda=self,
                numero=i + 1,
                valor=valor,
                data_vencimento=data,
                forma_pagamento=parcelas_payload[i].get('forma_pagamento'),
                observacao=parcelas_payload[i].get('observacao') or '',
                status='pendente'
            )
    
    def status_badge_class(self):
        return {
            'aberta': 'bg-secondary',
            'parcial': 'bg-warning',
            'em_atraso': 'bg-danger',
            'quitada': 'bg-success',
        }.get(self.status_financeiro, 'bg-secondary')
    
        
    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'Venda #{self.id} - {self.cliente}'

    
    criado_em = models.DateTimeField(auto_now_add=True)
    
            
    def __str__(self):
        return f'Venda #{self.id} - {self.cliente}'
    
    
    def save(self, *args, **kwargs):
        # 🔒 Fonte única da verdade: Orçamento aprovado
        if self.orcamento and self.valor_total <= Decimal('0.00'):
            self.valor_total = self.orcamento.total_com_desconto()
        super().save(*args, **kwargs)

    

# Parcelamento venda
class Parcelamento(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
    )
    
    STATUS_COBRANCA_CHOICES = (
        ('nao_enviado', 'Não enviado'),
        ('enviado', 'Enviado'),
        ('negociacao', 'Em negociação'),
    )
    status_cobranca = models.CharField(
        max_length=20,
        choices=STATUS_COBRANCA_CHOICES,
        default='nao_enviado',
        blank=True
    )
    
    venda = models.ForeignKey(
        'clientes.Venda',
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    
    numero = models.PositiveIntegerField(
        help_text='Número da parcela (1, 2, 3...)'
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    data_vencimento = models.DateField()
    
    forma_pagamento = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    
    status =models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )
    
    observacao = models.CharField(max_length=255, blank=True, null=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def esta_atrasada(self):
        '''
        Retorna True se a parcela estiver pendente e vencida.
        '''
        if self.status != 'pendente':
            return False
        
        if not self.data_vencimento:
            return False

        return self.data_vencimento < now().date()
    
    def dias_em_atraso(self):
        if self.status != 'pendente':
            return 0 
        
        if not self.data_vencimento:
            return 0
        
        hoje = now().date()
        
        if self.data_vencimento >= hoje:
            return 0
        
        return (hoje - self.data_vencimento).days
    
    def faixa_aging(self):
        dias = self.dias_em_atraso()
        
        if dias == 0:
            return None 
        
        if dias <= 30:
            return '0 - 30'
        elif dias <= 60:
            return '31 - 60'
        elif dias <= 90:
            return '61 - 90'
        else:
            return '90+'
    
    def aging_list():
        resultado = defaultdict(lambda: {
            'quantidade': 0,
            'valor_total': 0
        })
        
        parcelas = Parcelamento.objects.filter(
            status = 'pendente',
            data_vencimento__lt = now().date()
        )
        
        for parcela in parcelas:
            faixa = parcela.faixa_aging()
            if not faixa:
                continue
            
            resultado[faixa]['quantidade'] += 1
            resultado[faixa]['valor_total'] += parcela.valor
            
        return resultado
    
    class Meta:
        ordering = ['data_vencimento']
        
    def __str__(self):
        return f'Parcela {self.numero} - Venda #{self.venda.id}'

