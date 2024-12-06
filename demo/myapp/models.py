from django.db import models
from decimal import Decimal

class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Part(models.Model):
    number = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    picture_url = models.URLField(max_length=255, db_column='pictureURL', verbose_name="Picture URL")

    class Meta:
        managed = False  # This assumes `parts` table is pre-defined in the database
        db_table = 'parts'

    def __str__(self):
        return self.description


class Product(models.Model):
    number = models.IntegerField(unique=True)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    picture_url = models.URLField(max_length=255, verbose_name="Picture URL")
    available_quantity = models.PositiveIntegerField(default=100)  # Default available quantity

    def __str__(self):
        return self.description


class CustomUser(models.Model):
    email = models.EmailField(unique=True)  # Unique email for each user
    username = models.CharField(max_length=150, unique=True)  # Unique username
    password = models.CharField(max_length=128)  # Store hashed password
    name = models.CharField(max_length=255)  # Full name of the user

    def __str__(self):
        return self.username


class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')  # Link to CustomUser
    part = models.ForeignKey(Product, to_field='number', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    shipping_charge = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    handling_charge = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.part.description} - Quantity: {self.quantity}"

    @property
    def total_price(self):
        return self.part.price * self.quantity

    class Meta:
        ordering = ['part']


class Order(models.Model):
    STATUS_CHOICES = [
        ("Ordered", "Ordered"),
        ("Shipped", "Shipped"),
    ]

    # Existing fields
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_address = models.TextField()
    order_number = models.CharField(max_length=36, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_handling = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # New field for order status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Ordered",  # Default status is "Ordered"
    )

    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name} ({self.get_status_display()})"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.description} (Order {self.order.id})"


class Transaction(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    vendor = models.CharField(max_length=100)
    trans = models.CharField(max_length=100)
    cc = models.CharField(max_length=100)  # Credit Card Number
    name = models.CharField(max_length=100)
    exp = models.CharField(max_length=7)  # Expiry Date
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=50)
    authorization = models.CharField(max_length=100)
    timeStamp = models.BigIntegerField()

    def __str__(self):
        return f"{self.name} - {self.trans}"