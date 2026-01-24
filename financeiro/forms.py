from django import forms 
from financeiro.models import LancamentoFinanceiro



class LancamentoFinanceiroForm(forms.ModelForm):
    class Meta:
        model = LancamentoFinanceiro 
        fields = [
            'tipo',
            'data',
            'descricao',
            'valor',
        ]
        
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
