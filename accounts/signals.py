from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Perfil
from empresas.models import Empresa

User = get_user_model()


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        empresa = Empresa.objects.first()
        if empresa:
            Perfil.objects.create(
                user=instance,
                empresa=empresa,
                tipo='ADMIN' if instance.is_superuser else 'TECNICO'
            )
