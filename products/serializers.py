from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    qr_code = serializers.ImageField(read_only=True)
    
    class Meta:
        model = Product
        fields = "__all__"
        