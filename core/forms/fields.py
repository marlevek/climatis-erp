from django import forms
from core.utils.money import parse_money, quantize_money

class MoneyField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        if value in (None, ""):
            return None
        return quantize_money(parse_money(value))
