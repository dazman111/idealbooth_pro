from django.contrib import admin
from .models import Coupon, PromotionBanner


# --- Admin Coupon ---
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'actif', 'date_debut', 'date_fin')
    list_filter = ('actif', 'discount_type')
    search_fields = ('code',)
    readonly_fields = ('utilisations_effectuees',)


# --- Admin PromotionBanner ---
@admin.register(PromotionBanner)
class PromotionBannerAdmin(admin.ModelAdmin):
    list_display = ('message', 'promo_code', 'start_date', 'end_date', 'is_active')
