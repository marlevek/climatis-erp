from django.db import models



class LancamentoFinanceiro(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES
    )
    
    data = models.DateField()
    descricao = models.CharField(
        max_length=155
    )
    
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    
    origem = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Origem do lançamento (ex.: GestãoClick, Manual)'
    )
    
    referencia_externa = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text='ID ou referência do sistema de origem'
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data']
        
    def __str__(self): 
        return f"{self.data} - {self.get_tipo_display()} - {self.valor}"