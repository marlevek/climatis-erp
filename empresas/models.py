from django.db import models


class Empresa(models.Model):
    
    TIPO_PESSOA_CHOICES = (
        ('PJ', 'Pessoa Jurídica'),
        ('PF', 'Pessoa Física'),
    )
    
    REGIME_TRIBUTARIO_CHOICES = (
        ('simples', 'Simples Nacional'),
        ('presumido', 'Lucro Presumido'),
        ('real', 'Lucro Real'),
    )
    nome = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cnpj = models.CharField(max_length=18, unique=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES,
        default='PJ'
    )

    razao_social = models.CharField(
        max_length=200,
        blank=True,
        help_text="Obrigatório para PJ"
    )

    inscricao_estadual = models.CharField(
        max_length=30,
        blank=True
    )

    inscricao_municipal = models.CharField(
        max_length=30,
        blank=True
    )

    cnae_principal = models.CharField(
        max_length=20,
        blank=True,
        help_text="Ex: 4321-5/01"
    )

    regime_tributario = models.CharField(
        max_length=20,
        choices=REGIME_TRIBUTARIO_CHOICES,
        blank=True
    )

    # Endereço
    endereco = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=10, blank=True)

    # Identidade visual
    logo = models.ImageField(
        upload_to='empresas/logos/',
        blank=True,
        null=True
    )

    # Certificado digital (futuro NFS-e)
    certificado_digital = models.FileField(
        upload_to='empresas/certificados/',
        blank=True,
        null=True
    )

    certificado_senha = models.CharField(
        max_length=100,
        blank=True
    )

    def __str__(self):
        return self.nome_fantasia or self.nome
