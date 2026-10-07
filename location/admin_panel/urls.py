from django.urls import path
from . import views
from .views import CustomLoginView

app_name = "admin_panel"


urlpatterns = [

    #CONNEXION ADMIN
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('messages/', views.admin_messages, name='admin_messages'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path("logout/", views.admin_logout, name="logout"),

    #GESTION DES UTILISATEURS
    path('users/', views.manage_users, name='manage_users'),
    path("users/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("users/<int:user_id>/reactivate/", views.admin_reactivate_user, name="admin_reactivate_user"),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path("users/<int:user_id>/delete/", views.admin_delete_user, name="admin_delete_user"),
    
    #GESTION DES PHOTOBOOTHS
    path('photobooths/', views.manage_photobooths, name='manage_photobooths'),
    path('photobooths/add/', views.add_photobooth, name='add_photobooth'),
    path('photobooths/edit/<int:pk>/', views.edit_photobooth, name='edit_photobooth'),
    path('photobooths/delete/<int:pk>/', views.delete_photobooth, name='delete_photobooth'),
    
    path("photobooths/<int:pk>/restock/", views.restock_photobooth, name="restock_photobooth"),

    #GESTION DES ACCESSOIRES
    path("accessories/", views.accessory_list, name="accessory_list"),
    path("accessories/add/", views.add_accessory, name="add_accessory"),
    path("accessories/edit/<int:pk>/", views.edit_accessory, name="edit_accessory"),
    path("accessories/delete/<int:pk>/", views.delete_accessory, name="delete_accessory"),

    path('blog/', views.manage_blog, name='manage_blog'),
    

    path('payments/', views.manage_payments, name='manage_payments'),
    
    
    #GESTION DES RESEVATIONS
    path('reservations/', views.manage_reservations, name='manage_reservations'),
    path('reservations/update/', views.update_reservation_status, name='update_reservation_status'),
    path('reservations/<int:reservation_id>/detail/', views.reservation_detail, name='reservation_detail'),
    path('reservations/<int:reservation_id>/facture/', views.generate_invoice, name='generate_invoice'),
    path("reservations/<int:reservation_id>/facture/", views.admin_facture_detail, name="admin_facture_detail"),
    
    #GESTION DES COUPONS
    path("coupons/", views.manage_coupons, name="admin_coupon_list"),
    path("coupons/edit/<int:coupon_id>/", views.edit_coupon, name="admin_edit_coupon"),
    path("coupons/delete/<int:coupon_id>/", views.delete_coupon, name="admin_delete_coupon"),
    path("coupons/add/", views.add_coupon, name="add_coupon"),

    #Devis
    path("devis/", views.manage_devis, name="manage_devis"),
    path("devis/create/", views.create_devis, name="create_devis"),
    path("admin/devis/<int:devis_id>/valider/", views.valider_devis, name="admin_valider_devis"),
    path("admin/devis/<int:devis_id>/valider/", views.valider_devis, name="valider_devis"),
    path("devis/<int:devis_id>/", views.view_devis, name="view_devis"),

    #NOTIFICATION
    path('notifications/delete/<int:pk>/', views.adminpanel_delete_notification, name='delete_notification'),
    path('notifications/read/<int:pk>/', views.adminpanel_read_notification, name='read_notification'),

    #GESTION DES BANNIÈRES PROMO
    path("banners/", views.banner_list, name="banner_list"),
    path("banners/add/", views.add_banner, name="add_banner"),
    path("banners/edit/<int:pk>/", views.edit_banner, name="edit_banner"),
    path("banners/delete/<int:pk>/", views.delete_banner, name="delete_banner"),

    path('api/cancelled-count/', views.cancelled_count_api, name='cancelled_count_api'),


]
