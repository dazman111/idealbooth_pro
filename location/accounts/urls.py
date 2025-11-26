from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView



urlpatterns = [
    path('', views.home, name='home'),

    path('logout/', views.logout_view, name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),

   
]