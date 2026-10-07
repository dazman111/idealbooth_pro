from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordChangeDoneView

from rest_framework.routers import DefaultRouter

from . import views
from .views import CustomLoginView, CustomPasswordResetView
from photobooths.views import PhotoboothViewSet
from .views import devis_pdf 


app_name = "accounts"

# API Router
router = DefaultRouter()
router.register(r'photobooths', PhotoboothViewSet)


urlpatterns = [

    # --- Accueil ---
    path('', views.home, name='home'),

    # --- Authentification ---
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name="activate_account"),

    # --- Profil utilisateur ---
    path('mon-compte/', views.user_dashboard, name='user_dashboard'),
    path("cancel-reservation/<int:pk>/", views.cancel_reservation, name="cancel_reservation"),
    path('profile/', views.profile_view, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # --- Mot de passe ---
    path('change-password/', CustomPasswordResetView.as_view(), name='change_password'),
    path(
        'password-change-done/',
        PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done'
    ),

    # Reset password (Django)
    path(
        'password_reset_custom/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/registration/password_reset_form.html'
        ),
        name='password_reset_custom'
    ),
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/registration/password_reset_form.html'
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # --- Messages utilisateur ---
    path('messages/', views.user_messages, name='user_messages'),
    path('messages/conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('contact-admin/', views.contact_admin, name='contact_admin'),

    # --- Factures ---
    path("invoice/<int:reservation_id>/", views.generate_invoice, name="generate_invoice"),
    path("facture/<int:pk>/", views.invoice_detail, name="invoice_detail"),


    # --- Suppression de compte ---
    path("account/request-deletion/", views.request_account_deletion, name="request_account_deletion"),
    path("account/cancel-deletion/", views.cancel_account_deletion, name="cancel_account_deletion"),

    # --- Favoris ---
    path("dashboard/favorites/", views.user_favorites, name="user_favorites"),
    path("dashboard/favorites/toggle/<int:photobooth_id>/", views.toggle_favorite, name="toggle_favorite"),

    # --- Langue ---
    path('i18n/setlang/', views.set_language_ajax, name='set_language_ajax'),

    # --- Admin ---
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # --- Notification admin ---
    path('admin/notifications/read/<int:pk>/', views.admin_read_notification, name='admin_read_notification'),
    path('admin/notifications/delete/<int:pk>/', views.admin_delete_notification, name='admin_delete_notification'),
    
    # --- Notifications utilisateur ---
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),

    # --- Entreprise ---
    path('entreprise/dashboard/', views.entreprise_dashboard, name='entreprise_dashboard'),
    path('entreprise/reservations/', views.entreprise_reservations, name='entreprise_reservations'),


    # --- API ---
    path('api/', include(router.urls)),

    # --- Devis ---
    path('devis/generer/', views.generer_devis, name='generer_devis'),
    path('devis/pdf/<int:devis_id>/', views.devis_pdf, name='devis_pdf'),
   
    # --- ENTREPRISE : DEVIS ---
    path("entreprise/devis/", views.devis_list, name="devis_list"),
    path("entreprise/devis/<int:pk>/", views.devis_detail, name="devis_detail"),


    # --- ADMIN : DEVIS ---
    path("admin/devis/<int:devis_id>/valider/", views.valider_devis, name="valider_devis"),
    path("admin/devis/", views.admin_devis_list, name="admin_devis_list"),

    path('entreprise/info/', views.company_info, name='company_info'),
    path('entreprise/factures/', views.factures_list, name='factures_list'),
    path("entreprise/factures/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("entreprise/factures/<int:pk>/", views.invoice_detail, name="invoice_detail"),

]
