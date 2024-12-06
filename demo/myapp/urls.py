# urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.part_detail, name='part-detail'),  # Display all parts
    path('add_to_cart/<int:part_id>/', views.add_to_cart, name='add_to_cart'),  # Add item to cart
    path('cart/', views.cart_detail, name='cart_detail'),  # View cart
    path('checkout/', views.checkout, name='checkout'),  # Checkout
    path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),  # Increase quantity
    path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),  # Decrease quantity
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),  # Custom logout
    path('purchase_success/', views.purchase_success, name='purchase_success'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # path('warehouse-dashboard/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('warehouse/', views.warehouse_page, name='warehouse_page'),
    path('warehouse/', views.warehouse_orders, name='warehouse_orders'),
    path('warehouse/order/<int:order_id>/', views.order_details, name='order_details'),
    path('manage-products/', views.manage_products, name='manage_products'),
    path('manage-charges/', views.manage_charge, name='manage_charges'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<int:order_id>/', views.admin_order_details, name='admin_order_details'),

    # path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
]




