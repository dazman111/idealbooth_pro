# le coupon a ete modifier apres piratage
from django import forms
from photobooths.models import Photobooth  # ou le bon chemin vers le modèle
from coupons.models import Coupon, PromotionBanner


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

