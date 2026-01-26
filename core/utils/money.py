# core/utils/money.py
from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Union

MoneyLike = Union[str, int, float, Decimal]

def parse_money(value: MoneyLike, *, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """
    Converte entradas monetárias comuns para Decimal.
    Aceita formatos pt-BR como '1.250,00' e também '1250.00'.
    Retorna `default` (por padrão None) se value for vazio/None.
    Lança ValueError se não for possível converter.
    """
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        # converte via str para evitar ruídos binários do float
        return Decimal(str(value))

    s = str(value).strip()
    if s == "":
        return default

    # remove espaços e símbolo de moeda
    s = s.replace("R$", "").replace(" ", "")

    # Caso padrão BR: 1.234,56
    # Caso padrão US: 1,234.56 (menos provável, mas vamos tolerar)
    has_dot = "." in s
    has_comma = "," in s

    if has_dot and has_comma:
        # Decide qual é o separador decimal pelo último que aparece
        if s.rfind(",") > s.rfind("."):
            # BR: '.' milhar e ',' decimal
            s = s.replace(".", "").replace(",", ".")
        else:
            # US: ',' milhar e '.' decimal
            s = s.replace(",", "")
    elif has_comma and not has_dot:
        # 1234,56 -> 1234.56
        s = s.replace(",", ".")
    # else: já está em 1234.56 ou 1234

    try:
        return Decimal(s)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Valor monetário inválido: {value!r}") from e


def quantize_money(value: Optional[Decimal]) -> Optional[Decimal]:
    """Padroniza para 2 casas decimais."""
    if value is None:
        return None
    return value.quantize(Decimal("0.01"))


def excel_money(valor):
    if valor is None:
        return Decimal('0.00')
    return Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)