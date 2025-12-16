from .models import Message
from rest_framework.authtoken.models import Token

def unread_messages_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}

def auth_token(request):
    token = None
    if request.user.is_authenticated:
        token, _ = Token.objects.get_or_create(user=request.user)
    return {'auth_token': token.key if token else ''}