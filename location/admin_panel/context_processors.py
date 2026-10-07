from admin_panel.models import Message

def admin_unread_messages(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return {'admin_unread_messages': count}
    return {}
