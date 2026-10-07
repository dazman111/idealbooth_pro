from rest_framework import serializers
from .models import Photobooth, Accessory

class PhotoboothSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    accessories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Accessory.objects.all(),
        required=False
    )

    class Meta:
        model = Photobooth
        fields = '__all__'
