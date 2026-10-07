from admin_panel.models import Message
from coupons.models import PromotionBanner
from django.utils import timezone 

def admin_unread_messages(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return {'admin_unread_messages': count}
    return {}

def promo_banners(request):
    now = timezone.now()

    banners = PromotionBanner.objects.filter(
        start_date__lte=now,
        end_date__gte=now
    )

    return {'promo_banners': banners}