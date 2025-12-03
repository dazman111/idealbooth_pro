from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import date
from .models import Favorite

from .models import Photobooth
from .forms import PhotoboothForm
from reservations.models import Reservation
from reservations.forms import AddToCartForm  # ← Assure-toi que ce formulaire existe bien
from datetime import timedelta

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Photobooth
from .serializers import PhotoboothSerializer


from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date
# IMPORTANT : Assurez-vous d'importer votre modèle et votre fonction date.
# Exemple d'importation (adaptez selon la structure de votre projet) :
# from .models import Photobooth 
# from datetime import date # déjà présente

def photobooth_list(request):
    # 1. Récupération des paramètres de filtrage et de pagination
    query = request.GET.get("q", "")
    max_price = request.GET.get("max_price")
    available_only = request.GET.get("available")
    # CORRECTION: La variable page_number DOIT être récupérée au début.
    page_number = request.GET.get("page") 

    # 2. Initialisation du QuerySet (Tous les photobooths)
    # Assurez-vous que le modèle Photobooth est importé !
    photobooths = Photobooth.objects.all()

    # 3. Application des filtres
    if query:
        # Filtrage par nom OU description
        photobooths = photobooths.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if max_price:
        # Filtrage par prix maximum (gestion de l'erreur potentielle de conversion)
        try:
            photobooths = photobooths.filter(price__lte=max_price)
        except (ValueError, TypeError):
             # Ignorer ou gérer l'erreur si max_price n'est pas un nombre valide
             pass 

    if available_only:
        # Filtrage par disponibilité
        photobooths = photobooths.filter(available=True)
    
    # 4. Correction de l'avertissement de pagination : Ajout d'un ordre stable
    photobooths = photobooths.order_by('id') # Trier par ID pour une pagination fiable

    # 5. Pagination
    paginator = Paginator(photobooths, 6)  # 6 par page
    page_obj = paginator.get_page(page_number)

    # 6. Construction du contexte final (sans écraser les filtres)
    context = {
        # Données paginées
        "photobooths": page_obj, # La liste d'objets pour la page actuelle
        "page_obj": page_obj,    # L'objet Paginator pour les liens
        "is_paginated": page_obj.has_other_pages(),

        # Variables pour conserver l'état des filtres dans le formulaire HTML
        "query": query,
        "max_price": max_price,
        "available_only": available_only, # Passé comme chaîne 'on' ou None
        "today": date.today().isoformat(), # Utile pour les sélecteurs de date
    }
    
    return render(request, "photobooths/photobooth_list.html", context)



def photobooth_detail(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)
    form = AddToCartForm()

     # Vérifier si ce photobooth est déjà en favoris
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, photobooth=photobooth).exists()


    reservations = Reservation.objects.filter(photobooth=photobooth)
    disabled_dates = []
    for reservation in reservations:
        current_date = reservation.start_date
        while current_date <= reservation.end_date:
            disabled_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    return render(request, 'photobooths/photobooth_detail.html', {
        'photobooth': photobooth,
        'form': form,
        'disabled_dates': disabled_dates,
        'today': date.today(),  # ← ajoute ça ici
        'is_favorite': is_favorite, 
    })


@login_required
def photobooth_create(request):
    if request.method == 'POST':
        form = PhotoboothForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('photobooth_list')
    else:
        form = PhotoboothForm()
    return render(request, 'photobooths/photobooth_form.html', {'form': form})


@login_required
def photobooth_update(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)
    if request.method == 'POST':
        form = PhotoboothForm(request.POST, request.FILES, instance=photobooth)
        if form.is_valid():
            form.save()
            return redirect('photobooth_list')
    else:
        form = PhotoboothForm(instance=photobooth)
    return render(request, 'photobooths/photobooth_form.html', {'form': form})


@login_required
def photobooth_delete(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)
    if request.method == 'POST':
        photobooth.delete()
        return redirect('photobooth_list')
    return render(request, 'photobooths/photobooth_confirm_delete.html', {'photobooth': photobooth})


@login_required
def dashboard(request):
    query = request.GET.get('q')
    available_only = request.GET.get('available') == '1'

    photobooths = Photobooth.objects.all()

    if query:
        photobooths = photobooths.filter(name__icontains=query)

    if available_only:
        photobooths = photobooths.filter(available=True)

    count = photobooths.count()

    return render(request, 'photobooths/dashboard.html', {
        'photobooths': photobooths,
        'query': query,
        'available_only': available_only,
        'count': count,
    })


def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def add_photobooth(request):
    if request.method == 'POST':
        form = PhotoboothForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('photobooth_list')
    else:
        form = PhotoboothForm()
    return render(request, 'photobooths/add_photobooth.html', {'form': form})

def add_to_cart(request, photobooth_id):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        photobooth = get_object_or_404(Photobooth, pk=photobooth_id)

        selected_date = parse_date(date_str)
        if not selected_date:
            messages.error(request, "Date invalide.")
            return redirect('photobooth_list')

        cart = request.session.get('cart', [])

        # Optionnel : vérifier si cet item existe déjà
        for item in cart:
            if item['photobooth_id'] == photobooth.id and item['date'] == date_str:
                messages.warning(request, "Ce photobooth est déjà dans votre panier pour cette date.")
                return redirect('photobooth_list')

        cart.append({
            "photobooth_id": photobooth.id,
            "name": photobooth.name,
            "price": float(photobooth.price),
            "date": date_str,
            "image_url": photobooth.image.url if photobooth.image else '/static/img/default.jpg'
        })
        request.session['cart'] = cart
        messages.success(request, f"{photobooth.name} ajouté au panier pour le {date_str}.")
        return redirect('photobooth_list')
    
class PhotoboothViewSet(viewsets.ModelViewSet):
    queryset = Photobooth.objects.all()
    serializer_class = PhotoboothSerializer
    permission_classes = [IsAuthenticated]

@login_required
def notify_me(request, photobooth_id):
    photobooth = get_object_or_404(Photobooth, id=photobooth_id)
    # Ici tu peux ajouter l'utilisateur à une liste d'attente ou envoyer un email
    messages.success(request, "Vous serez notifié lorsque le photobooth sera disponible.")
    return redirect('photobooth_list')

@staff_member_required
def restock_photobooth(request, booth_id):
    booth = get_object_or_404(Photobooth, id=booth_id)
    booth.available = 1  # Remet à 1 disponible
    booth.stock = max(booth.stock, 1)  # Si stock total à 0, on le met à 1 aussi
    booth.save()
    messages.success(request, f"Le photobooth '{booth.name}' a été réapprovisionné.")
    return redirect('manage_photobooths')

@login_required
def add_favorite(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)

    Favorite.objects.get_or_create(
        user=request.user,
        photobooth=photobooth
    )

    # Retourne 200 en rechargeant la page photobooth détail
    return render(
        request,
        'photobooths/photobooth_detail.html',
        {
            'photobooth': photobooth,
            'favorite_added': True,
        },
        status=200
    )

@login_required
def remove_favorite(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)

    Favorite.objects.filter(
        user=request.user,
        photobooth=photobooth
    ).delete()

    return render(
        request,
        'photobooths/photobooth_detail.html',
        {
            'photobooth': photobooth,
            'favorite_removed': True,
        },
        status=200
    )

@login_required
def toggle_favorite(request, pk):
    photobooth = get_object_or_404(Photobooth, pk=pk)

    favorite = Favorite.objects.filter(user=request.user, photobooth=photobooth)

    if favorite.exists():
        favorite.delete()
        status_msg = "removed"
    else:
        Favorite.objects.create(user=request.user, photobooth=photobooth)
        status_msg = "added"

    # Toujours 200 — aucune redirection
    return render(
        request,
        "accounts/user_favorites_toggle.html",
        {
            "photobooth": photobooth,
            "status": status_msg
        },
        status=200
    )

