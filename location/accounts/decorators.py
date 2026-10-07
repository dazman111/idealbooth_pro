from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from functools import wraps


def account_protection(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if user.is_authenticated:
            account_age = timezone.now() - user.date_joined

            # Si le compte a moins de 30 jours → accès restreint
            if account_age < timedelta(days=30):
                return redirect("account_protection_notice")

        return view_func(request, *args, **kwargs)

    return wrapper
