from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import routers
from reservations.views import ReservationViewSet
from photobooths.views import PhotoboothViewSet

router = routers.DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'photobooths', PhotoboothViewSet, basename='photobooth')


urlpatterns_i18n = i18n_patterns(
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('cart/', include('cart.urls')),
    path('photobooths/', include('photobooths.urls')),
    path('reservations/', include(('reservations.urls', 'reservation'), namespace='reservation')),
    path('blog/', include('blog.urls')),
    prefix_default_language=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include(router.urls)),
    path('api/token/', obtain_auth_token),
    path('api-auth/', include('rest_framework.urls')),
    path("stripe/webhook/", include("cart.webhook_urls")),
]

urlpatterns += urlpatterns_i18n

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
