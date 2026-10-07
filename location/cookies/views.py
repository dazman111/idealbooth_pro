from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CookieConsentLog
from django.shortcuts import render

@require_POST
def save_cookie_consent(request):
    choice = request.POST.get("choice", "essential")
    analytics = request.POST.get("analytics") == "true"
    marketing = request.POST.get("marketing") == "true"
    personalization = request.POST.get("personalization") == "true"

    CookieConsentLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        choice=choice,
        analytics=analytics,
        marketing=marketing,
        personalization=personalization,
    )

    response = JsonResponse({"status": "ok"})
    response.set_cookie("cookie_consent", choice, max_age=60*60*24*365)
    response.set_cookie("cookie_analytics", str(analytics).lower(), max_age=60*60*24*365)
    response.set_cookie("cookie_marketing", str(marketing).lower(), max_age=60*60*24*365)
    response.set_cookie("cookie_personalization", str(personalization).lower(), max_age=60*60*24*365)

    return response

def cookie_policy(request):
    return render(request, "cookies/politique_cookies.html")