import json
import uuid
import requests
from datetime import datetime
from django.http import JsonResponse
from .forms import CheckoutForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Part, Product, CartItem, CustomUser,Order, OrderItem, Transaction


def sync_products_from_legacy():
    """
    Syncs parts from the legacy database to the Product table.
    """
    legacy_parts = Part.objects.using('legacy').all()
    for part in legacy_parts:
        Product.objects.get_or_create(
            number=part.number,
            defaults={
                'description': part.description,
                'price': part.price,
                'weight': part.weight,
                'picture_url': part.picture_url,
                'available_quantity': 100,  # Set default available quantity
            }
        )


def part_detail(request):
    """
    Displays available products with quantities.
    """
    sync_products_from_legacy()  # Sync legacy parts to the Product table
    products = Product.objects.all()
    return render(request, 'part_detail.html', {'products': products})

def add_to_cart(request, part_id):
    """
    Add a part to the cart without altering the available_quantity yet.
    """
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first to add items to the cart.")
        return redirect('login')

    user_id = request.session.get('user_id')
    user = get_object_or_404(CustomUser, id=user_id)
    part = get_object_or_404(Product, id=part_id)

    if part.available_quantity < 1:
        messages.error(request, f"{part.description} is out of stock.")
        return redirect('part-detail')

    cart_item, created = CartItem.objects.get_or_create(part=part, user=user)
    if created:
        cart_item.save()
        messages.success(request, f"{part.description} was added to the cart.")
    else:
        messages.info(request, f"{part.description} is already in your cart.")

    return redirect('cart_detail')


def cart_detail(request):
    """
    Displays cart items for the logged-in user.
    """
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in to view the cart.")
        return redirect('login')

    user_id = request.session.get('user_id')
    user = get_object_or_404(CustomUser, id=user_id)
    cart_items = CartItem.objects.filter(user=user)
    total_price = sum(item.total_price for item in cart_items)

    return render(request, 'cart_detail.html', {'cart_items': cart_items, 'total_price': total_price})


# Increase Quantity View
def increase_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.quantity += 1
    cart_item.save()
    messages.success(request, f"{cart_item.part.description} quantity increased to {cart_item.quantity}.")
    return redirect('cart_detail')


# Decrease Quantity View
def decrease_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, f"{cart_item.part.description} quantity decreased to {cart_item.quantity}.")
    else:
        cart_item.delete()
        messages.info(request, f"{cart_item.part.description} removed from the cart.")
    return redirect('cart_detail')

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')  # Create a template for the admin dashboard
# def warehouse_dashboard(request):
#     return render(request, 'warehouse_page.html')  # Create a template for the warehouse dashboard



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Hardcoded credentials for Admin and Warehouse Worker
        if username == "admin" and password == "admin123":
            # Redirect to Admin page
            messages.success(request, "Welcome, Admin!")
            return redirect('admin_dashboard')  # Define a URL or view for Admin Dashboard
        elif username == "warehouse" and password == "warehouse123":
            # Redirect to Warehouse Worker page
            messages.success(request, "Welcome, Warehouse Worker!")
            return redirect('warehouse_page')  # Define a URL or view for Warehouse Dashboard

        # Standard user login process
        try:
            # Check if the username exists
            user = CustomUser.objects.get(username=username)

            # Check if the password matches
            if user.password == password:
                # Log the user in and create a session
                request.session['user_id'] = user.id
                request.session['username'] = user.username  # Store the username in the session
                messages.success(request, f"Welcome, {user.name}!")
                return redirect('part-detail')  # Redirect to part_detail page
            else:
                # Password is incorrect
                messages.error(request, "Incorrect password. Please try again.")
                return redirect('login')  # Reload the login page

        except CustomUser.DoesNotExist:
            # If the username does not exist, display an error
            messages.error(request, "Username does not exist. Please register.")
            return redirect('register')  # Redirect to the register page

    return render(request, 'login.html')




# Register View
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        name = request.POST.get('name')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        user = CustomUser(username=username, email=email, password=password, name=name)
        user.save()
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        messages.success(request, "Registration successful! Welcome to the site.")
        return redirect('part-detail')

    return render(request, 'register.html')


# Logout View
def custom_logout(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('part-detail')

from .models import CartItem, Order, OrderItem, Product, CustomUser
import uuid

from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CartItem, CustomUser, Order, OrderItem
from .forms import CheckoutForm

def checkout(request):
    handling_fee = Decimal("5.00")  # Fixed handling charge
    per_unit_weight_shipping_cost = Decimal("10.00")  # Per unit weight shipping cost

    # Check if the user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "You need to log in to proceed with checkout.")
        return redirect('login')

    user = get_object_or_404(CustomUser, id=user_id)

    # Fetch cart items for the logged-in user
    cart_items = CartItem.objects.filter(user=user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart_detail')

    # Calculate total costs
    total_weight = sum(item.part.weight * item.quantity for item in cart_items)
    total_price = sum(item.total_price for item in cart_items)
    shipping_charge = total_weight * per_unit_weight_shipping_cost
    handling_charge = handling_fee
    total_cost = total_price + shipping_charge + handling_charge

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Process valid form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            address = form.cleaned_data['address']

            # Create an order
            order = Order.objects.create(
                customer_name=name,
                customer_email=email,
                customer_address=address,
                total_amount=total_cost,
                shipping_handling=shipping_charge + handling_charge,
                order_number=str(uuid.uuid4()),
                status="Ordered",
            )

            # Create order items and update available quantities
            for item in cart_items:
                product = item.part
                if product.available_quantity >= item.quantity:
                    product.available_quantity -= item.quantity  # Decrement here
                    product.save()

                    # Add to order items
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item.quantity,
                        total_price=item.total_price,
                    )
                else:
                    messages.error(request, f"Insufficient stock for {product.description}.")
                    return redirect('cart_detail')

            # Clear the user's cart
            cart_items.delete()

            # Confirmation message
            messages.success(request, f"Order {order.order_number} placed successfully!")
            return redirect('part-detail')
        else:
            # Form errors
            messages.error(request, "There was an error with your form. Please check your inputs.")
    else:
        # Display form with cart details
        form = CheckoutForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_charge': shipping_charge,
        'handling_charge': handling_charge,
        'total_cost': total_cost,
    }
    return render(request, 'checkout.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order

# Warehouse Page View
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order

# def warehouse_page(request):
#     # Check if the user is a warehouse worker
#     # if request.session.get('username') != 'warehouse':  # Replace with the warehouse worker's username
#     #     messages.error(request, "Unauthorized access.")
#     #     return redirect('login')
#
#     if request.method == 'POST':
#         order_id = request.POST.get('order_id')
#         new_status = request.POST.get('status')
#         try:
#             order = get_object_or_404(Order, id=order_id)
#             if new_status in dict(Order.STATUS_CHOICES):  # Validate status
#                 order.status = new_status
#                 order.save()
#                 return JsonResponse({'success': True, 'message': f"Order {order.order_number} status updated to {new_status}."})
#             else:
#                 return JsonResponse({'success': False, 'message': "Invalid status."})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)})
#
#     # Fetch all orders for display
#     orders = Order.objects.all()
#     return render(request, 'warehouse_page.html', {'orders': orders})

from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order

def warehouse_page(request):
    # Check if the user is a warehouse worker
    # if request.session.get('username') != 'warehouse_worker':  # Replace with the warehouse worker's username
    #     messages.error(request, "Unauthorized access.")
    #     return redirect('login')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        try:
            order = get_object_or_404(Order, id=order_id)
            if new_status in dict(Order.STATUS_CHOICES):  # Validate status
                order.status = new_status
                order.save()

                # Send email if status is "Shipped"
                if new_status == "Shipped":
                    send_mail(
                        subject="Order Shipped: {}".format(order.order_number),
                        message=(
                            f"Dear {order.customer_name},\n\n"
                            f"Your order {order.order_number} has been shipped.\n\n"
                            f"Thank you for shopping with us!\n\n"
                            f"Best regards,\nYour Store Team"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.customer_email],
                        fail_silently=False,
                    )

                return JsonResponse({'success': True, 'message': f"Order {order.order_number} status updated to {new_status}."})
            else:
                return JsonResponse({'success': False, 'message': "Invalid status."})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # Fetch all orders for display
    orders = Order.objects.all()
    return render(request, 'warehouse_page.html', {'orders': orders})

from django.shortcuts import render, get_object_or_404
from .models import Order, OrderItem

def warehouse_orders(request):
    """
    View to list all orders.
    """
    orders = Order.objects.all().order_by('-created_at')  # List orders, newest first
    return render(request, 'warehouse_orders.html', {'orders': orders})

from django.shortcuts import render, get_object_or_404
from .models import Order, OrderItem

def order_details(request, order_id):
    """
    View to display details of a specific order.
    """
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_details.html', {'order': order, 'order_items': order_items})


# Update Order Status
# def update_order_status(request, order_id):
#     # Check if user is a warehouse worker
#     if request.session.get('username') != 'warehouse_worker':
#         messages.error(request, "Unauthorized access.")
#         return redirect('login')
#
#     order = get_object_or_404(Order, id=order_id)
#
#     if request.method == 'POST':
#         new_status = request.POST.get('status')
#         if new_status in dict(Order.STATUS_CHOICES):
#             order.status = new_status
#             order.save()
#             messages.success(request, f"Order {order.order_number} status updated to {new_status}.")
#         else:
#             messages.error(request, "Invalid status.")
#     return redirect('warehouse_page')


def purchase_success(request):
    return render(request, 'purchase_success.html')

def purchase_failure(request):
    return render(request, 'purchase_failure.html')