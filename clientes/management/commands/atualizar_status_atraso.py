from django.core.management.base import BaseCommand
from django.utils.timezone import now
from clientes.models import Venda

class Command(BaseCommand):
    help = 'Atualiza status financeiro das vendas com parcelas em atraso'

    def handle(self, *args, **options):
        vendas = Venda.objects.all()
        atualizadas = 0

        for venda in vendas:
            novo_status = venda.calcular_status_financeiro()
            if venda.status_financeiro != novo_status:
                venda.status_financeiro = novo_status
                venda.save(update_fields=['status_financeiro'])
                atualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{atualizadas} vendas atualizadas'
            )
        )
