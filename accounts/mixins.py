from django.shortcuts import redirect
from empresas.models import Empresa
from accounts.models import Perfil


class PerfilRequiredMixin:
    """
    Garante que o usuário autenticado tenha um Perfil válido.
    Cria automaticamente se faltar.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect('login')

        try:
            user.perfil
        except Perfil.DoesNotExist:
            empresa = Empresa.objects.first()
            if not empresa:
                raise Exception("Nenhuma empresa cadastrada no sistema.")

            Perfil.objects.create(
                user=user,
                empresa=empresa,
                tipo='ADMIN' if user.is_superuser else 'TECNICO'
            )

        return super().dispatch(request, *args, **kwargs)
