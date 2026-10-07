from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from .views import restock_photobooth

from rest_framework.routers import DefaultRouter
from .views import PhotoboothViewSet

#API séparée
router = DefaultRouter()
router.register(r'photobooths', PhotoboothViewSet)

urlpatterns = [


    #Liste des photobooths (page principale)
    path('', views.photobooth_list, name='photobooth_list'),

    #Notifications
    path('<int:photobooth_id>/notify/', views.notify_me, name='notify_me'),

    #Admin restock
    path('admin/photobooth/<int:booth_id>/restock/', restock_photobooth, name='restock_photobooth'),

    #Favoris
    path('favorite/add/<int:pk>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:pk>/', views.remove_favorite, name='remove_favorite'),

    #CRUD
    path('<int:pk>/', views.photobooth_detail, name='photobooth_detail'),
    path('add/', views.photobooth_create, name='photobooth_create'),
    path('<int:pk>/edit/', views.photobooth_update, name='photobooth_update'),
    path('<int:pk>/delete/', views.photobooth_delete, name='photobooth_delete'),
    path('dashboard/', views.dashboard, name='dashboard'),

    #API propre, séparée
    path('api/', include(router.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
