from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart,CartItem
from .serializers import CartSerializer, AddToCartSerializer, CartItemSerializer,UpdateCartItemSerializer

from products.models import Product

from django.shortcuts import get_object_or_404

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.GenericAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. Get product ID and quantity
        product_id = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        # 2. Find the product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3. Validate stock
        if quantity > product.stock:
            return Response(
                {"detail": "Insufficient stock available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Get or create the user's cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # 5. Find the existing cart item
        cart_item = CartItem.objects.filter(
            cart=cart,
            product=product,
        ).first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return Response(
                    {"detail": "Insufficient stock available for the requested quantity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save(update_fields=["quantity"])

        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
            )
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED,
        )
        
 
class RemoveCartItemView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user
        )

class UpdateCartItemView(generics.UpdateAPIView):
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user
        )
    def perform_update(self,serializer):
        requested_quantity = serializer.validated_data['quantity']
        available_stock = serializer.instance.product.stock
        
        if requested_quantity > available_stock:
            raise serializers.ValidationError({
                "quantity":"Insufficient stock available."
            })
        serializer.save()
