from django.db import models
from empresas.models import Empresa 


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
