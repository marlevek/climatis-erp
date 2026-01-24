import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from financeiro.models import LancamentoFinanceiro


class Command(BaseCommand):
    help = "Importa Contas a Receber do GestãoClick (Excel)"

    def handle(self, *args, **options):
        BASE_DIR = Path(__file__).resolve().parents[3]
        caminho_arquivo = BASE_DIR / "importacoes" / "relatorio_contas_receber.xlsx"

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

        # mantém apenas linhas com valor válido
        df = df[df["valor_normalizado"].notna()]

        total_importados = 0

        for _, row in df.iterrows():
            valor = row["valor_normalizado"]

            data_vencimento = row.get("Unnamed: 9")
            data = pd.to_datetime(data_vencimento, errors="coerce", dayfirst=True)

            if pd.isna(data):
                continue

            data = data.date()

            cliente = str(row.get("Unnamed: 3", "")).strip()
            documento = str(row.get("Unnamed: 4", "")).strip()

            descricao = cliente
            if documento:
                descricao += f" ({documento})"

            LancamentoFinanceiro.objects.create(
                tipo="entrada",
                data=data,
                descricao=descricao,
                valor=valor,
                origem="GestãoClick",
            )

            total_importados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {total_importados} entradas importadas."
            )
        )
