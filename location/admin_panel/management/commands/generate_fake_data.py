import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# ✔️ Tes vrais modèles
from photobooths.models import Photobooth, Favorite
from reservations.models import Reservation
from blog.models import Article, Comment, ArticleLikes
from coupons.models import Coupon
from admin_panel.models import (
    Payment,
    Message,
    Coupon as OldCoupon,
    AdminNotification,
    Accessory,
    Devis
)

User = get_user_model()


class Command(BaseCommand):
    help = "Génère toutes les données fake"

    def handle(self, *args, **kwargs):

        # -----------------------------------------
        # 1) Récupération des données existantes
        # -----------------------------------------
        users = list(User.objects.all())
        articles = list(Article.objects.all())
        coupons = list(Coupon.objects.all())

        # -----------------------------------------
        # 2) Génération de 30 entreprises
        # -----------------------------------------
        for i in range(30):
            base_username = f"entreprise_auto_{i+1}"
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            User.objects.create_user(
                username=username,
                email=f"{username}@test.com",
                password="Test1234!",
                account_type="company",
                company_name=f"Entreprise Auto {i+1}",
                company_address=f"Rue Auto {i+1}, 1000 Bruxelles",
                company_vat_number=f"BE0{i+1}2345678"
            )

        users = list(User.objects.all())  # refresh après création

        # -----------------------------------------
        # 3) 100 Photobooths
        # -----------------------------------------
        for i in range(100):
            Photobooth.objects.create(
                name=f"Photobooth Auto #{i+1}",
                description="Photobooth généré automatiquement.",
                price=random.randint(150, 500),
                image="photobooths/default.jpg",
                stock=random.randint(1, 3)
            )

        photobooths = list(Photobooth.objects.all())

        # -----------------------------------------
        # 4) 100 Réservations
        # -----------------------------------------
        for _ in range(100):
            user = random.choice(users)
            booth = random.choice(photobooths)

            start = timezone.now() + timedelta(days=random.randint(1, 60))
            end = start + timedelta(hours=4)

            Reservation.objects.create(
                user=user,
                photobooth=booth,
                start_date=start,
                end_date=end,
                quantity=1,
                status="confirmed"
            )

        # -----------------------------------------
        # 5) 100 Favoris Photobooth
        # -----------------------------------------
        for _ in range(100):
            Favorite.objects.get_or_create(
                user=random.choice(users),
                photobooth=random.choice(photobooths)
            )

        # -----------------------------------------
        # 6) 100 Commentaires Blog
        # -----------------------------------------
        if articles:
            for _ in range(100):
                Comment.objects.create(
                    user=random.choice(users),
                    article=random.choice(articles),
                    content=f"Commentaire auto-généré #{random.randint(1,9999)}",
                    rating=random.randint(1, 5)
                )

        # -----------------------------------------
        # 7) 100 Likes Blog
        # -----------------------------------------
        if articles:
            for _ in range(100):
                ArticleLikes.objects.get_or_create(
                    customuser=random.choice(users),
                    article=random.choice(articles)
                )

        # -----------------------------------------
        # 8) 100 utilisations de coupons (nouveau modèle)
        # -----------------------------------------
        if coupons:
            for _ in range(100):
                c = random.choice(coupons)
                u = random.choice(users)
                c.users_used.add(u)
                c.utilisations_effectuees += 1
                c.save()

        # -----------------------------------------
        # 9) 100 Payments
        # -----------------------------------------
        for i in range(100):
            Payment.objects.create(
                user=random.choice(users),
                amount=random.randint(10, 500),
                status=random.choice(["paid", "pending", "failed"])
            )

        # -----------------------------------------
        # 10) 100 Messages internes
        # -----------------------------------------
        for i in range(100):
            sender = random.choice(users)
            recipient = random.choice([u for u in users if u != sender])

            Message.objects.create(
                sender=sender,
                recipient=recipient,
                subject=f"Sujet auto {i+1}",
                body=f"Message généré automatiquement #{i+1}"
            )

        # -----------------------------------------
        # 11) 100 Coupons (ancienne version admin_panel)
        # -----------------------------------------
        for i in range(100):
            OldCoupon.objects.create(
                code=f"AUTO{i+1}",
                discount_percent=random.choice([None, random.randint(5, 50)]),
                discount_amount=random.choice([None, random.randint(5, 30)]),
                expiration_date=timezone.now().date() + timedelta(days=random.randint(10, 300)),
                is_active=True
            )

        # -----------------------------------------
        # 12) 100 Admin Notifications
        # -----------------------------------------
        for i in range(100):
            AdminNotification.objects.create(
                message=f"Notification admin auto #{i+1}",
                user=random.choice(users)
            )

        # -----------------------------------------
        # 13) 100 Devis
        # -----------------------------------------
        for i in range(100):
            entreprise = random.choice([u for u in users if u.account_type == "company"])
            client = random.choice([u for u in users if u.account_type == "user"])

            prix_ht = random.randint(100, 800)
            tva = 21
            prix_ttc = prix_ht + (prix_ht * tva / 100)

            Devis.objects.create(
                entreprise=entreprise,
                client=client,
                admin=random.choice(users),
                numero=f"DV-AUTO-{i+1}",
                description="Prestation Photobooth auto-générée",
                duree=random.randint(1, 3),
                prix_ht=prix_ht,
                tva=tva,
                prix_ttc=prix_ttc,
                status=random.choice(["pending", "accepted", "refused"])
            )



        self.stdout.write(self.style.SUCCESS(" Toutes les données fake ont été générées avec succès !"))
