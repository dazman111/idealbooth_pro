from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_fix_message_columns'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Migration neutralisée car les champs 'receiver', 'sender' et 'subject'
        # existent déjà ou ont été modifiés manuellement dans la base.
        # On laisse cette migration vide pour éviter les erreurs.
    ]
