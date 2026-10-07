from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
            model = Reservation
            fields = ['start_date', 'end_date','photobooth', 'start_date', 'end_date', 'event_type', 'accessories', 'quantity',]
            widgets = {
                'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                'accessories': forms.CheckboxSelectMultiple(),
            }

class AddToCartForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget)
    quantity = forms.IntegerField(min_value=1, initial=1)
