from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('clientes/', include('clientes.urls')),
    path('enderecos/', include('enderecos.urls')),
    
    
    path('', RedirectView.as_view(url='/clientes/', permanent=False)),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.BASE_DIR / 'static'
    )
