from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from photobooths.views import PhotoboothViewSet
from .views import CustomPasswordResetView
from django.contrib.auth.views import PasswordChangeDoneView
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

app_name = "accounts"

router = DefaultRouter()
router.register(r'photobooths', PhotoboothViewSet)

urlpatterns = [
    path('', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name="activate_account"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('mon-compte/', views.user_dashboard, name='user_dashboard'),

    path('logout/', views.logout_view, name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),

    path('profile/', views.profile_view, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', CustomPasswordResetView.as_view(), name='change_password'),
    path('password-change-done/', PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),

    path('contact-admin/', views.contact_admin, name='contact_admin'),
    path("invoice/<int:reservation_id>/", views.generate_invoice, name="generate_invoice"),
    path("account/request-deletion/", views.request_account_deletion, name="request_account_deletion"),
    path("account/cancel-deletion/", views.cancel_account_deletion, name="cancel_account_deletion"),


    path('password_reset_custom/', auth_views.PasswordResetView.as_view(template_name='accounts/registrationpassword_reset_form.html'), name='password_reset_custom'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/registration/password_reset_complete.html'), name='password_reset_complete'),

    path('messages/', views.user_messages, name='user_messages'),

    path("dashboard/favorites/", views.user_favorites, name="user_favorites"),
    path("dashboard/favorites/toggle/<int:photobooth_id>/", views.toggle_favorite, name="toggle_favorite"),
    
    path('i18n/setlang/', views.set_language_ajax, name='set_language_ajax'),
    
    # REST API sous /api/
    path('api/', include(router.urls)),

]