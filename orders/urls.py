from django.urls import path
from .views import PlaceOrderView
from .views import (
    PlaceOrderView,
    CreateRazorpayOrderView,
    VerifyPaymentView,
)

urlpatterns = [
    path("orders/checkout/", PlaceOrderView.as_view(), name="checkout"),
    path(
    "orders/<int:order_id>/payment/",
    CreateRazorpayOrderView.as_view(),
    name="create-payment",
),
    path(
    "orders/<int:order_id>/verify-payment/",
    VerifyPaymentView.as_view(),
    name="verify-payment",
),
]