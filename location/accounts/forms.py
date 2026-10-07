from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import CustomUser

User = get_user_model()


# --- Formulaire d’inscription ---
class CustomUserCreationForm(UserCreationForm):
    account_type = forms.ChoiceField(
        choices=CustomUser.ACCOUNT_TYPES,
        label="Type de compte"
    )

    # Champs entreprise
    company_name = forms.CharField(required=False, label="Nom de l'entreprise")
    company_vat_number = forms.CharField(required=False, label="Numéro TVA")
    company_address = forms.CharField(required=False, label="Adresse professionnelle")

    accept_terms = forms.BooleanField(
        label="J'accepte les politiques de confidentialité et les mentions légales",
        error_messages={
            'required': "Vous devez accepter les politiques et mentions légales pour créer un compte."
        }
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'profile_picture', 'account_type',
            'company_name', 'company_vat_number', 'company_address'
        ]

    def clean(self):
        cleaned_data = super().clean()
        account_type = cleaned_data.get("account_type")

        # Champs obligatoires si entreprise
        if account_type == "company":
            if not cleaned_data.get("company_name"):
                self.add_error("company_name", "Ce champ est obligatoire pour un compte entreprise.")
            if not cleaned_data.get("company_address"):
                self.add_error("company_address", "Ce champ est obligatoire pour un compte entreprise.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Sécurité : forcer les flags sensibles
        user.is_active = False  # Activation par email
        user.is_staff = False   # Jamais staff à la création
        user.is_superuser = False  # Jamais superuser à la création

        # Champs entreprise
        user.account_type = self.cleaned_data["account_type"]
        user.company_name = self.cleaned_data.get("company_name")
        user.company_vat_number = self.cleaned_data.get("company_vat_number")
        user.company_address = self.cleaned_data.get("company_address")

        if commit:
            user.save()
        return user


# --- Formulaire de modification de profil ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'profile_picture',
            'company_name', 'company_vat_number', 'company_address'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'heure_livraison': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.TextInput(attrs={'class': 'form-control'}),

            }

        labels = {
            'address': "Adresse (domicile)",
            'heure_livraison': "Heure de livraison / installation préférée",
            'company_address': "Adresse de l'entreprise",
        
        }
        
    def clean(self):
        cleaned_data = super().clean()

        # Empêcher un utilisateur simple d’ajouter des infos entreprise
        if self.instance.account_type != "company":
            cleaned_data['company_name'] = None
            cleaned_data['company_vat_number'] = None
            cleaned_data['company_address'] = None

        return cleaned_data

# --- Formulaire de contact ---
class ContactForm(forms.Form):
    subject = forms.CharField(max_length=200, label="Sujet")
    message = forms.CharField(widget=forms.Textarea, label="Message")


# --- Changer le mot de passe sans ancien mot de passe ---
class PasswordResetWithoutOldForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirmez le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, user):
        """Met à jour le mot de passe de l'utilisateur."""
        password = self.cleaned_data["new_password1"]
        user.set_password(password)
        user.save()
        return user
