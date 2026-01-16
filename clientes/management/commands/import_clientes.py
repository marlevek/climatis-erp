from django.core.management.base import BaseCommand
from clientes.models import Cliente
from enderecos.models import Endereco
from empresas.models import Empresa
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Importa clientes a partir de múltiplos arquivos XLSX (GestãoClick)'

    def add_arguments(self, parser):
        parser.add_argument(
            'pasta',
            type=str,
            help='Caminho da pasta com arquivos XLSX'
        )

    def handle(self, *args, **options):
        empresa = Empresa.objects.first()

        if not empresa:
            self.stdout.write(self.style.ERROR(
                'Nenhuma empresa cadastrada. Crie uma empresa antes de importar.'
            ))
            return

        pasta = options['pasta']

        if not os.path.isdir(pasta):
            self.stdout.write(self.style.ERROR('Pasta inválida'))
            return

        arquivos = [
            f for f in os.listdir(pasta)
            if f.lower().endswith('.xlsx')
        ]

        if not arquivos:
            self.stdout.write(self.style.ERROR(
                'Nenhum arquivo XLSX encontrado'))
            return

        total_criados = 0
        total_ignorados = 0

        for arquivo in arquivos:
            caminho = os.path.join(pasta, arquivo)
            self.stdout.write(f'📄 Importando {arquivo}...')

            df = pd.read_excel(caminho)

            for _, row in df.iterrows():
                cnpj = str(row.get('CNPJ', '')).strip()
                cpf = str(row.get('CPF', '')).strip()

                documento = cnpj if cnpj and cnpj != 'nan' else cpf
                if not documento or documento == 'nan':
                    total_ignorados += 1
                    continue

                tipo = 'PJ' if cnpj and cnpj != 'nan' else 'PF'


                cliente, created = Cliente.objects.get_or_create(
                    documento=documento,
                    empresa=empresa,
                    defaults={
                        'tipo_pessoa': tipo,
                        'nome': row.get('Razão social') if tipo == 'PJ' else row.get('Nome/Nome fantasia'),
                        'nome_fantasia': row.get('Nome/Nome fantasia', '') if tipo == 'PJ' else '',
                        'email': row.get('E-mail', ''),
                        'telefone': row.get('Celular') or row.get('Telefone', ''),
                        'ativo': True if row.get('Ativo') == 'Sim' else False,
                    }
                )

                if created:
                    total_criados += 1

                    Endereco.objects.create(
                        cliente=cliente,
                        cep=str(row.get('CEP', '')).strip(),
                        logradouro=row.get('Logradouro', ''),
                        numero=str(row.get('Número', '')).strip(),
                        complemento=row.get('Complemento', ''),
                        bairro=row.get('Bairro', ''),
                        cidade=row.get('Cidade', ''),
                        estado=row.get('Estado', ''),
                    )
                else:
                    total_ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✔ Importação finalizada\n'
            f'Clientes criados: {total_criados}\n'
            f'Ignorados (duplicados/sem documento): {total_ignorados}'
        ))
