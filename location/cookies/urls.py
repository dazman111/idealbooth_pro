from django.urls import path
from .views import save_cookie_consent, cookie_policy

urlpatterns = [
    path("consent/", save_cookie_consent, name="save_cookie_consent"),
    path("politique/", cookie_policy, name="politique_cookies"),
]
