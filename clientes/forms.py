from django import forms 
from .models import Cliente 
from clientes.models import OrcamentoItem
from core.forms.fields import MoneyField



class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa',
            'nome',
            'nome_fantasia',
            'documento',
            'email',
            'telefone',
            'ativo',
        ]
        
        widgets = {
            'tipo_pessoa': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_pessoa')
        nome_fantasia = cleaned_data.get('nome_fantasia')
        
        if tipo == 'PJ' and not nome_fantasia:
            self.add_error(
                'nome_fantasia',
                'Nome fantasia é obrigatório pra Pessoa Jurídica'
            )
        return cleaned_data


class OrcamentoItemForm(forms.ModelForm):
    class Meta:
        model = OrcamentoItem
        fields = [
            'quantidade',
            'valor_unitario',
            'desconto_percentual',
            'desconto_valor',
            'descricao',
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'placeholder': ''}),
        }


class PagamentoRealForm(forms.Form):
    valor_pagamento = MoneyField(required=False)
