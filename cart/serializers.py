from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']
        read_only_fields = ['id']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class AddToCartSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    
    def validate_quantity(self,value):
        if value <= 0:
            raise serializers.ValidationError("quantity must be greater than zero")
        return value
    
    def update(self, instance, validated_data):
        instance.quantity = validated_data.get(
            "quantity",
            instance.quantity,
        )
        instance.save(update_fields=["quantity"])
        return instance