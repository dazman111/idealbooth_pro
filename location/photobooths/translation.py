from modeltranslation.translator import register, TranslationOptions
from .models import Photobooth

@register(Photobooth)
class PhotoboothTranslationOptions(TranslationOptions):
    fields = ('description',)
