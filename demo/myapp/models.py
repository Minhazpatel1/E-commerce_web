from django.db import models

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


class CustomUser(models.Model):
    email = models.EmailField(unique=True)  # Unique email for each user
    username = models.CharField(max_length=150, unique=True)  # Unique username
    password = models.CharField(max_length=128)  # Store hashed password
    name = models.CharField(max_length=255)  # Full name of the user

    def __str__(self):
        return self.username

class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')  # Link to CustomUser
    part = models.ForeignKey(Part, to_field='number', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.part.description} - Quantity: {self.quantity}"

    @property
    def total_price(self):
        return self.part.price * self.quantity

    class Meta:
        ordering = ['part']



# class Order(models.Model):
#     customer_name = models.CharField(max_length=255)
#     customer_email = models.EmailField()
#     customer_address = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=50, choices=[('authorized', 'Authorized'), ('shipped', 'Shipped')])
#
#     def __str__(self):
#         return f"Order {self.id} - {self.customer_name}"