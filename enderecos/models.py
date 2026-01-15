from django.db import models
from clientes.models import Cliente 


class Endereco(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='enderecos'
    )
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.logradouro}, {self.numero}, {self.cidade}'