from django.db import models
from django.db.models import Max
from empresas.models import Empresa 
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
