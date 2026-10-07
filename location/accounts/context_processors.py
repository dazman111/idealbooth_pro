from admin_panel.models import Message
from rest_framework.authtoken.models import Token


def unread_messages_count(request):
    """Retourne le nombre de messages non lus pour l'utilisateur connecté."""
    if request.user.is_authenticated:
        return {
            'unread_messages_count': Message.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        }

    return {'unread_messages_count': 0}


def auth_token(request):
    """Retourne le token d'authentification API de l'utilisateur."""
    if request.user.is_authenticated:
        token, _ = Token.objects.get_or_create(user=request.user)
        return {'auth_token': token.key}

    return {'auth_token': ''}
