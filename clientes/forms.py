from django import forms 
from .models import Cliente 


class ClienteForm(forms.ModelForm):
    class Meta:
        fields = [
            'tipo_pessoa',
            'nome',
            'nome_fantasia',
            'documento',
            'email',
            'telefone',
            'ativo',
        ]
        
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