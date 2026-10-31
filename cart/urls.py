from django.urls import path
from .views import CartView,AddToCartView,RemoveCartItemView,UpdateCartItemView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/items/<int:pk>/',RemoveCartItemView.as_view(),name='remove-cart-item'),
    path('cart/items/<int:pk>/update/',UpdateCartItemView.as_view(),name='update-cart-item'),  
]