from django.db import models

# Create your models here.
class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

from django.db import models


from django.db import models

class Part(models.Model):
    number = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    picture_url = models.URLField(max_length=255, db_column='pictureURL')  # Correcting field name

    class Meta:
        managed = False
        db_table = 'parts'