# le coupon a ete modifier apres piratage
from django import forms
from photobooths.models import Photobooth  # ou le bon chemin vers le modèle
from .models import Coupon


class PhotoboothForm(forms.ModelForm):
    class Meta:
        model = Photobooth
        fields = ['name', 'description', 'price', 'image']


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code", "discount_percent", "discount_amount", "expiration_date", "is_active"]

    def clean(self):
        cleaned_data = super().clean()
        percent = cleaned_data.get("discount_percent")
        amount = cleaned_data.get("discount_amount")

        if not percent and not amount:
            raise forms.ValidationError("Vous devez définir une réduction en % ou un montant.")
        if percent and amount:
            raise forms.ValidationError("Ne mettez PAS les deux : choisissez % OU montant.")

        return cleaned_data

