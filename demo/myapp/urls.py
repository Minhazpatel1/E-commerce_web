# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.part_detail, name='part-detail'),  # Display all parts
    path('add_to_cart/<int:part_id>/', views.add_to_cart, name='add_to_cart'),  # Add item to cart
    path('cart/', views.cart_detail, name='cart_detail'),  # View cart
    path('checkout/', views.checkout, name='checkout'),
]
