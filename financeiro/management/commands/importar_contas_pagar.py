import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from financeiro.models import LancamentoFinanceiro
from django.utils.dateparse import parse_date


class Command(BaseCommand):
    help = "Importa Contas a Pagar do GestãoClick (Excel)"
    
    def handle(self, *args, **options):
        from pathlib import Path
        import pandas as pd
        from financeiro.models import LancamentoFinanceiro

        BASE_DIR = Path(__file__).resolve().parents[3]
        caminho_arquivo = BASE_DIR / "importacoes" / "relatorio_contas_pagar.xlsx"

        self.stdout.write("Lendo arquivo Excel...")
        df = pd.read_excel(caminho_arquivo)

        # --------------------------------
        # NORMALIZA VALOR (FORMATO BR)
        # --------------------------------
        df["valor_normalizado"] = (
            df["Unnamed: 16"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )

        df["valor_normalizado"] = pd.to_numeric(
            df["valor_normalizado"], errors="coerce"
        )

        # mantém apenas linhas válidas (remove cabeçalhos e lixo)
        df = df[df["valor_normalizado"].notna()]

        total_importados = 0

        # --------------------------------
        # LOOP DE IMPORTAÇÃO
        # --------------------------------
        for _, row in df.iterrows():
            valor = row["valor_normalizado"]

            data_pagamento = row.get("Unnamed: 10")
            data_vencimento = row.get("Unnamed: 9")

            data = data_pagamento if pd.notna(data_pagamento) else data_vencimento
            data = pd.to_datetime(data, errors="coerce")

            if pd.isna(data):
                continue

            data = data.date()

            descricao = str(row.get("Unnamed: 3", "")).strip()
            plano_contas = str(row.get("Unnamed: 4", "")).strip()

            descricao_final = descricao
            if plano_contas:
                descricao_final += f" ({plano_contas})"

            LancamentoFinanceiro.objects.create(
                tipo="saida",
                data=data,
                descricao=descricao_final,
                valor=valor,
                origem="GestãoClick",
            )

            total_importados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {total_importados} saídas importadas."
            )
        )

