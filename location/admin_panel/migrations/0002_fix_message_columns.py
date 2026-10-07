from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0001_initial'),
    ]

    operations = [
        # Cette migration est volontairement vide car
        # les champs subject, sender et receiver existent déjà
        # dans la base de données. On neutralise donc l'ajout
        # pour éviter l'erreur "Nom du champ déjà utilisé".
    ]
