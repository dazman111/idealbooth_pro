# le coupon a ete modifier apres piratage
from django import forms
from photobooths.models import Photobooth  # ou le bon chemin vers le modèle
from coupons.models import Coupon, PromotionBanner
from django import forms
from accounts.models import Devis
from admin_panel.models import Accessory
from django.contrib.auth import get_user_model


User = get_user_model()

class PhotoboothForm(forms.ModelForm):
    class Meta:
        model = Photobooth
        fields = ['name', 'description', 'price', 'image']


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code", "description", "discount_type", "discount_value",
                  "date_debut", "date_fin", "actif", "utilisation_max"]

    
class PromotionBannerForm(forms.ModelForm):
    class Meta:
        model = PromotionBanner
        fields = ["message", "promo_code", "start_date", "end_date"]


class DevisForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(account_type="company"),
        label="Client",
        required=True
    )

    class Meta:
        model = Devis
        fields = [
            "client",
            "description",
            "duree",
            "prix_ht",
            "tva",
            "prix_ttc",
        ]

class AccessoryForm(forms.ModelForm):
    class Meta:
        model = Accessory
        fields = ["photobooth", "name", "image", "category"]