from django.db import models
from django.conf import settings 
from empresas.models import Empresa 


class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('TECNICO', 'Técnico'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='usuarios'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default='TECNICO'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({self.empresa})'
