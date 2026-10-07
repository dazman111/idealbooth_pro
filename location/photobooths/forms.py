from django import forms
from .models import Photobooth, Accessory

class PhotoboothForm(forms.ModelForm):
    class Meta:
        model = Photobooth
        fields = [
            'name',
            'description',
            'price',
            'image',
            'stock',
            'available',
            'accessories',
        ]
        widgets = {
            'accessories': forms.CheckboxSelectMultiple(),
        }

class AccessoryForm(forms.ModelForm):
    class Meta:
        model = Accessory
        fields = ['name', 'price', 'description', 'image']

