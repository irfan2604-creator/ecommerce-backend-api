from decimal import Decimal

import razorpay

from django.conf import settings
from django.db import transaction

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, inline_serializer

from cart.models import Cart, CartItem
from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderSerializer, VerifyPaymentSerializer


def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="create_order",
        summary="Create an order",
        description="Creates an order using the authenticated user's cart.",
        request=None,
        responses={
            201: OrderSerializer,
        },
    )
    def post(self, request):
        with transaction.atomic():
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return Response(
                    {"detail": "Cart not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            cart_items = CartItem.objects.filter(cart=cart).select_related(
                "product"
            )

            if not cart_items.exists():
                return Response(
                    {"detail": "Your cart is empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total_amount = Decimal("0.00")
            products_to_order = []

            for item in cart_items:
                product = Product.objects.select_for_update().get(
                    id=item.product_id
                )

                if item.quantity > product.stock:
                    return Response(
                        {
                            "detail": (
                                f"Insufficient stock for {product.name}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                total_amount += product.price * item.quantity

                products_to_order.append(
                    {
                        "product": product,
                        "quantity": item.quantity,
                        "price": product.price,
                    }
                )

            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
            )

            order_items = [
                OrderItem(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=item["price"],
                )
                for item in products_to_order
            ]

            OrderItem.objects.bulk_create(order_items)

            serializer = OrderSerializer(order)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )


class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="create_razorpay_order",
        summary="Create Razorpay order",
        description=(
            "Creates a Razorpay payment order for an existing Django order."
        ),
        request=None,
        responses={
            201: inline_serializer(
                name="RazorpayOrderResponse",
                fields={
                    "order_id": serializers.IntegerField(),
                    "razorpay_order_id": serializers.CharField(),
                    "amount": serializers.IntegerField(),
                    "currency": serializers.CharField(),
                    "key": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.payment_status == Order.PaymentStatus.PAID:
            return Response(
                {"detail": "This order has already been paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {"detail": "This order cannot be paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.razorpay_order_id:
            return Response(
                {"detail": "Razorpay order already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = get_razorpay_client()

        razorpay_order = client.order.create(
            {
                "amount": int(order.total_amount * 100),
                "currency": "INR",
                "receipt": f"order_{order.id}",
            }
        )

        order.razorpay_order_id = razorpay_order["id"]
        order.save(update_fields=["razorpay_order_id"])

        return Response(
            {
                "order_id": order.id,
                "razorpay_order_id": razorpay_order["id"],
                "amount": int(order.total_amount * 100),
                "currency": "INR",
                "key": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="verify_razorpay_payment",
        summary="Verify Razorpay payment",
        description=(
            "Verifies the Razorpay payment signature and updates "
            "the order and inventory."
        ),
        request=VerifyPaymentSerializer,
        responses={
            200: inline_serializer(
                name="PaymentVerificationResponse",
                fields={
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def post(self, request, order_id):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razorpay_order_id = serializer.validated_data[
            "razorpay_order_id"
        ]
        razorpay_payment_id = serializer.validated_data[
            "razorpay_payment_id"
        ]
        razorpay_signature = serializer.validated_data[
            "razorpay_signature"
        ]

        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.payment_status == Order.PaymentStatus.PAID:
            return Response(
                {"detail": "Payment has already been verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.payment_status == Order.PaymentStatus.REFUND_REQUIRED:
            return Response(
                {"detail": "This order requires a refund."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != Order.Status.PENDING:
            return Response(
                {"detail": "This order cannot be verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.razorpay_order_id != razorpay_order_id:
            return Response(
                {"detail": "Invalid Razorpay order ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = get_razorpay_client()

        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except razorpay.errors.SignatureVerificationError:
            return Response(
                {"detail": "Invalid payment signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = client.payment.fetch(razorpay_payment_id)

        if payment["status"] != "captured":
            return Response(
                {"detail": "Payment has not been captured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment["order_id"] != order.razorpay_order_id:
            return Response(
                {"detail": "Payment does not belong to this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_amount = int(order.total_amount * 100)

        if payment["amount"] != expected_amount:
            return Response(
                {"detail": "Payment amount does not match the order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment["currency"] != "INR":
            return Response(
                {"detail": "Invalid payment currency."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            order = Order.objects.select_for_update().get(
                id=order_id,
                user=request.user,
            )

            if order.payment_status == Order.PaymentStatus.PAID:
                return Response(
                    {"detail": "Payment has already been verified."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if order.status != Order.Status.PENDING:
                return Response(
                    {"detail": "This order cannot be verified."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order_items = list(
                OrderItem.objects.filter(order=order).select_related(
                    "product"
                )
            )

            product_ids = [item.product_id for item in order_items]

            locked_products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(
                    id__in=product_ids
                )
            }

            required_quantities = {}

            for item in order_items:
                required_quantities[item.product_id] = (
                    required_quantities.get(item.product_id, 0)
                    + item.quantity
                )

            for product_id, quantity in required_quantities.items():
                product = locked_products[product_id]

                if product.stock < quantity:
                    order.payment_status = (
                        Order.PaymentStatus.REFUND_REQUIRED
                    )
                    order.razorpay_payment_id = razorpay_payment_id
                    order.save(
                        update_fields=[
                            "payment_status",
                            "razorpay_payment_id",
                        ]
                    )

                    return Response(
                        {
                            "detail": (
                                "Payment captured, but stock is insufficient. "
                                "Refund required."
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

            for product_id, quantity in required_quantities.items():
                product = locked_products[product_id]
                product.stock -= quantity
                product.save(update_fields=["stock"])

            try:
                cart = Cart.objects.get(user=request.user)

                for product_id, quantity in required_quantities.items():
                    cart_item = CartItem.objects.filter(
                        cart=cart,
                        product_id=product_id,
                    ).first()

                    if cart_item:
                        if cart_item.quantity > quantity:
                            cart_item.quantity -= quantity
                            cart_item.save(update_fields=["quantity"])
                        else:
                            cart_item.delete()

            except Cart.DoesNotExist:
                pass

            order.razorpay_payment_id = razorpay_payment_id
            order.payment_status = Order.PaymentStatus.PAID
            order.status = Order.Status.CONFIRMED

            order.save(
                update_fields=[
                    "razorpay_payment_id",
                    "payment_status",
                    "status",
                ]
            )

        return Response(
            {
                "detail": (
                    "Payment verified and order confirmed successfully."
                )
            },
            status=status.HTTP_200_OK,
        )