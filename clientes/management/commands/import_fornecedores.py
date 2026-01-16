from django.core.management.base import BaseCommand
from clientes.models import Fornecedor
from empresas.models import Empresa
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Importa fornecedores a partir de múltiplos arquivos XLSX (GestãoClick)'

    def add_arguments(self, parser):
        parser.add_argument(
            'pasta',
            type=str,
            help='Caminho da pasta com arquivos XLSX de fornecedores'
        )

    def handle(self, *args, **options):
        pasta = options['pasta']

        if not os.path.isdir(pasta):
            self.stdout.write(self.style.ERROR('Pasta inválida'))
            return

        empresa = Empresa.objects.first()
        if not empresa:
            self.stdout.write(self.style.ERROR(
                'Nenhuma empresa cadastrada. Crie uma empresa antes de importar.'
            ))
            return

        arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.xlsx')]

        if not arquivos:
            self.stdout.write(self.style.ERROR('Nenhum arquivo XLSX encontrado'))
            return

        criados = 0
        ignorados = 0

        for arquivo in arquivos:
            caminho = os.path.join(pasta, arquivo)
            self.stdout.write(f'📄 Importando {arquivo}...')

            df = pd.read_excel(caminho)

            for _, row in df.iterrows():
                cnpj = str(row.get('CNPJ', '')).strip()
                cpf = str(row.get('CPF', '')).strip()

                documento = cnpj if cnpj and cnpj != 'nan' else cpf
                if not documento or documento == 'nan':
                    ignorados += 1
                    continue

                tipo = 'PJ' if cnpj and cnpj != 'nan' else 'PF'

                fornecedor, created = Fornecedor.objects.get_or_create(
                    documento=documento,
                    empresa=empresa,
                    defaults={
                        'tipo_pessoa': tipo,
                        'nome': row.get('Razão social') if tipo == 'PJ' else row.get('Nome/Nome fantasia'),
                        'email': row.get('E-mail', ''),
                        'telefone': row.get('Celular') or row.get('Telefone', ''),
                        'ativo': True if row.get('Ativo') == 'Sim' else False,
                    }
                )

                if created:
                    criados += 1
                else:
                    ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✔ Importação de fornecedores finalizada\n'
            f'Fornecedores criados: {criados}\n'
            f'Ignorados (duplicados/sem documento): {ignorados}'
        ))
