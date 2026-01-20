from django.db.models.signals import post_save, post_delete 
from django.dispatch import receiver 
from .models import Parcelamento 
from django.db import transaction


# Após pagar parcela
@receiver(post_save, sender=Parcelamento)
def atualizar_status_venda_apos_salvar_parcela(sender, instance, **kwargs):
    venda = instance.venda
    
    transaction.on_commit(
        lambda: venda.atualizar_status_financeiro()
    )
    

# Após excluir parcela
@receiver(post_delete, sender=Parcelamento)
def atualizar_status_venda_apos_excluir_parcela(sender, instance, **kwargs):
    venda = instance.venda 
   
    transaction.on_commit(
       lambda: venda.atualizar_status_financeiro()
   )

