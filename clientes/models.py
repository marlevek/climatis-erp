from django.db import models
from django.db.models import Max
from empresas.models import Empresa 
from decimal import Decimal
import re 


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
        """
        Soma dos subtotais dos itens (com desconto por item).
        """
        return sum(
            (item.subtotal() for item in self.itens.all()),
            Decimal('0.00')
        )
        
    def valor_desconto_geral(self):
        """
        Calcula o desconto aplicado AO ORÇAMENTO INTEIRO.
        """
        total = self.total_itens()

        if not self.desconto_tipo or self.desconto_valor <= 0:
            return Decimal('0.00')

        if self.desconto_tipo == 'percentual':
            return (total * self.desconto_valor) / Decimal('100')

        return min(self.desconto_valor, total)

    def total_com_desconto(self):
        """
        Total final do orçamento (itens - desconto geral).
        """
        return max(
            self.total_itens() - self.valor_desconto_geral(),
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
        null=True,
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
        on_delete=models.CASCADE,
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

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'Venda #{self.id} - {self.cliente}'

    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data']
        
    def __str__(self):
        return f'Venda #{self.id} - {self.cliente}'
    

# Parcelamento venda
class Parcelamento(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('paga', 'Paga'),
        ('cancelada', 'Cancelada'),
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
    
    class Meta:
        ordering = ['data_vencimento']
        
    def __str__(self):
        return f'Parcela {self.numero} - Venda #{self.venda.id}'

