from django.contrib import admin
from .models import Photobooth
from .models import Accessory


@admin.register(Photobooth)
class PhotoboothAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')

@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


