from django.db import models
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File
from django.urls import reverse

class Category(models.Model):
    
    name = models.CharField(max_length=100,unique =True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category,on_delete=models.PROTECT,related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='product_qrcodes/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def generate_qr_code(self):
        product_url = f"{settings.SITE_URL}/api/products/{self.id}/"

        qr = qrcode.make(product_url)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        file_name = f"product_{self.id}_qr.png"

        self.qr_code.save(
            file_name,
            File(buffer),
            save=False
        )

        buffer.close()