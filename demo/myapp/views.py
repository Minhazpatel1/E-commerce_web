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

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from .models import Order

from decimal import Decimal
from django.db.models import Avg
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order

# def manage_charges(request):


# def manage_charges(request):
#     # Calculate average charges across all orders
#     shipping_charge_avg = Order.objects.aggregate(Avg('shipping_charge'))['shipping_charge__avg'] or Decimal('0.00')
#     handling_charge_avg = Order.objects.aggregate(Avg('handling_charge'))['handling_charge__avg'] or Decimal('0.00')
#
#     # Default charges if no orders exist or average isn't applicable
#     default_shipping_charge = Decimal('10.00')  # Define a default shipping charge
#     default_handling_charge = Decimal('5.00')   # Define a default handling charge
#
#     current_shipping_charge = shipping_charge_avg if shipping_charge_avg > 0 else default_shipping_charge
#     current_handling_charge = handling_charge_avg if handling_charge_avg > 0 else default_handling_charge
#
#     if request.method == 'POST':
#         # Get new values from the form
#         new_shipping_charge = Decimal(request.POST.get('shipping_charge', current_shipping_charge))
#         new_handling_charge = Decimal(request.POST.get('handling_charge', current_handling_charge))
#
#         # Update all orders with the new charges
#         Order.objects.update(shipping_charge=new_shipping_charge, handling_charge=new_handling_charge)
#
#         messages.success(request, "Charges updated successfully!")
#         return redirect('manage_charges')
#
#     return render(request, 'manage_charges.html', {
#         'current_shipping_charge': current_shipping_charge,
#         'current_handling_charge': current_handling_charge,
#     })


#
# def manage_charges(request):
#     if request.method == 'POST':
#         try:
#             # Get new charges from the form
#             shipping_charge = Decimal(request.POST.get('shipping_charge'))
#             handling_charge = Decimal(request.POST.get('handling_charge'))
#
#             # Update all existing orders
#             Order.objects.all().update(
#                 shipping_charge=shipping_charge,
#                 handling_charge=handling_charge,
#             )
#
#             messages.success(request, "Shipping and handling charges updated successfully!")
#         except Exception as e:
#             messages.error(request, f"Error updating charges: {str(e)}")
#
#     # Pass the current charges for display
#     latest_order = Order.objects.order_by('-created_at').first()
#     current_shipping_charge = latest_order.shipping_charge if latest_order else Decimal('0.00')
#     current_handling_charge = latest_order.handling_charge if latest_order else Decimal('0.00')
#
#     return render(request, 'manage_charges.html', {
#         'current_shipping_charge': current_shipping_charge,
#         'current_handling_charge': current_handling_charge,
#     })

# def checkout(request):
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate total costs using the model methods
#     total_price = sum(item.total_price for item in cart_items)
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_price,
#                 shipping_charge=sum(item.calculate_shipping_charge() for item in cart_items),
#                 handling_charge=sum(item.calculate_handling_charge() for item in cart_items),
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#     }
#     return render(request, 'checkout.html', context)

# def checkout(request):
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate total costs using the model methods
#     total_price = sum(item.total_price for item in cart_items)
#     shipping_charge = sum(item.shipping_charge for item in cart_items)  # Sum up shipping charges
#     handling_charge = sum(item.handling_charge for item in cart_items)  # Sum up handling charges
#     total_cost = total_price + shipping_charge + handling_charge
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_price,
#                 shipping_charge=shipping_charge,
#                 handling_charge=handling_charge,
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'shipping_charge': shipping_charge,
#         'handling_charge': handling_charge,
#         'total_cost': total_cost,
#     }
#     return render(request, 'checkout.html', context)

# def checkout(request):
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate charges using CartItem model methods
#     total_price = sum(item.total_price for item in cart_items)  # Total price of items
#     shipping_charge = sum(item.calculate_shipping_charge() for item in cart_items)  # Dynamic shipping charge
#     handling_charge = sum(item.calculate_handling_charge() for item in cart_items)  # Dynamic handling charge
#     total_cost = total_price + shipping_charge + handling_charge  # Total cost
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_cost,
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'shipping_charge': shipping_charge,
#         'handling_charge': handling_charge,
#         'total_cost': total_cost,
#     }
#     return render(request, 'checkout.html', context)

# def checkout(request):
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate charges using CartItem model methods
#     total_price = sum(item.total_price for item in cart_items)  # Total price of items
#     shipping_charge = sum(item.calculate_shipping_charge() for item in cart_items)  # Dynamic shipping charge
#     handling_charge = sum(item.calculate_handling_charge() for item in cart_items)  # Dynamic handling charge
#     total_cost = total_price + shipping_charge + handling_charge  # Total cost
#
#     # Concatenate shipping and handling charges for the order
#     shipping_handling_charge = f"Shipping: ${shipping_charge:.2f}, Handling: ${handling_charge:.2f}"
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_cost,
#                 shipping_handling_charge=shipping_handling_charge,
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'shipping_charge': shipping_charge,
#         'handling_charge': handling_charge,
#         'total_cost': total_cost,
#     }
#     return render(request, 'checkout.html', context)

def checkout(request):
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

    # Calculate charges using CartItem model methods
    total_price = sum(item.total_price for item in cart_items)  # Total price of items
    shipping_charge = sum(item.calculate_shipping_charge() for item in cart_items)  # Dynamic shipping charge
    handling_charge = sum(item.calculate_handling_charge() for item in cart_items)  # Dynamic handling charge
    shipping_handling = shipping_charge + handling_charge  # Combine shipping and handling
    total_cost = total_price + shipping_handling  # Total cost

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
                shipping_handling=shipping_handling,  # Correct field name
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

from django.shortcuts import render
from .models import Order
from django.db.models import Q
from datetime import datetime

def admin_orders(request):
    """
    View to display all orders and support filtering based on date range, status, or price range.
    """
    # Fetch filters from GET parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Base queryset
    orders = Order.objects.all()

    # Apply filters
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        orders = orders.filter(created_at__date__range=(start, end))

    if status:
        orders = orders.filter(status=status)

    if min_price:
        orders = orders.filter(total_amount__gte=min_price)

    if max_price:
        orders = orders.filter(total_amount__lte=max_price)

    context = {
        'orders': orders,
        'STATUS_CHOICES': Order.STATUS_CHOICES,
    }

    return render(request, 'admin_orders.html', context)


# def checkout(request):
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate charges using CartItem model methods
#     total_price = sum(item.total_price for item in cart_items)  # Total price of items
#     shipping_charge = sum(item.calculate_shipping_charge() for item in cart_items)  # Dynamic shipping charge
#     handling_charge = sum(item.calculate_handling_charge() for item in cart_items)  # Dynamic handling charge
#     total_cost = total_price + shipping_charge + handling_charge  # Total cost
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_cost,
#                 shipping_charge=shipping_charge,
#                 handling_charge=handling_charge,
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'shipping_charge': shipping_charge,
#         'handling_charge': handling_charge,
#         'total_cost': total_cost,
#     }
#     return render(request, 'checkout.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Product
from decimal import Decimal

def admin_order_details(request, order_id):
    """
    View to display details of a specific order including its items.
    """
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()  # Related OrderItem objects

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'admin_order_details.html', context)


from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CartItem

def manage_charge(request):
    """
    View to allow the admin to manage shipping and handling charges.
    """
    # Default values for charges
    current_shipping_charge = Decimal("10.00")  # Default shipping charge
    current_handling_charge = Decimal("5.00")  # Default handling charge

    if request.method == "POST":
        # Get values from the form
        shipping_charge = request.POST.get('shipping_charge')
        handling_charge = request.POST.get('handling_charge')

        try:
            # Update charges globally for all cart items
            CartItem.objects.update(
                shipping_charge=Decimal(shipping_charge),
                handling_charge=Decimal(handling_charge),
            )
            messages.success(request, "Shipping and handling charges updated successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    # Get the charges from any cart item (assuming charges are the same for all cart items)
    cart_item = CartItem.objects.first()
    if cart_item:
        current_shipping_charge = cart_item.shipping_charge
        current_handling_charge = cart_item.handling_charge

    context = {
        'current_shipping_charge': current_shipping_charge,
        'current_handling_charge': current_handling_charge,
    }
    return render(request, 'manage_charges.html', context)


# def manage_charge(request):
#     """
#     View to allow the admin to manage shipping and handling charges.
#     """
#     # if not request.session.get('is_admin'):  # Check if the user is an admin
#     #     messages.error(request, "You do not have permission to access this page.")
#     #     return redirect('login')
#
#     # Default values for charges
#     current_shipping_charge = Decimal("10.00")  # Default shipping charge
#     current_handling_charge = Decimal("5.00")  # Default handling charge
#
#     if request.method == "POST":
#         # Get values from the form
#         shipping_charge = request.POST.get('shipping_charge')
#         handling_charge = request.POST.get('handling_charge')
#
#         try:
#             # Update charges globally for all products
#             Product.objects.update(
#                 shipping_charge=Decimal(shipping_charge),
#                 handling_charge=Decimal(handling_charge),
#             )
#             messages.success(request, "Shipping and handling charges updated successfully.")
#         except Exception as e:
#             messages.error(request, f"An error occurred: {e}")
#
#     # Get the charges from any product (assuming charges are the same for all products)
#     product = Product.objects.first()
#     if product:
#         current_shipping_charge = product.shipping_charge
#         current_handling_charge = product.handling_charge
#
#     context = {
#         'current_shipping_charge': current_shipping_charge,
#         'current_handling_charge': current_handling_charge,
#     }
#     return render(request, 'manage_charges.html', context)


# def checkout(request):
#     handling_fee = Decimal("5.00")  # Fixed handling charge
#     per_unit_weight_shipping_cost = Decimal("10.00")  # Per unit weight shipping cost
#
#     # Check if the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You need to log in to proceed with checkout.")
#         return redirect('login')
#
#     user = get_object_or_404(CustomUser, id=user_id)
#
#     # Fetch cart items for the logged-in user
#     cart_items = CartItem.objects.filter(user=user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty.")
#         return redirect('cart_detail')
#
#     # Calculate total costs
#     total_weight = sum(item.part.weight * item.quantity for item in cart_items)
#     total_price = sum(item.total_price for item in cart_items)
#     shipping_charge = total_weight * per_unit_weight_shipping_cost
#     handling_charge = handling_fee
#     total_cost = total_price + shipping_charge + handling_charge
#
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Process valid form data
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             address = form.cleaned_data['address']
#
#             # Create an order
#             order = Order.objects.create(
#                 customer_name=name,
#                 customer_email=email,
#                 customer_address=address,
#                 total_amount=total_cost,
#                 shipping_handling=shipping_charge + handling_charge,
#                 order_number=str(uuid.uuid4()),
#                 status="Ordered",
#             )
#
#             # Create order items and update available quantities
#             for item in cart_items:
#                 product = item.part
#                 if product.available_quantity >= item.quantity:
#                     product.available_quantity -= item.quantity  # Decrement here
#                     product.save()
#
#                     # Add to order items
#                     OrderItem.objects.create(
#                         order=order,
#                         product=product,
#                         quantity=item.quantity,
#                         total_price=item.total_price,
#                     )
#                 else:
#                     messages.error(request, f"Insufficient stock for {product.description}.")
#                     return redirect('cart_detail')
#
#             # Clear the user's cart
#             cart_items.delete()
#
#             # Confirmation message
#             messages.success(request, f"Order {order.order_number} placed successfully!")
#             return redirect('part-detail')
#         else:
#             # Form errors
#             messages.error(request, "There was an error with your form. Please check your inputs.")
#     else:
#         # Display form with cart details
#         form = CheckoutForm()
#
#     context = {
#         'form': form,
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'shipping_charge': shipping_charge,
#         'handling_charge': handling_charge,
#         'total_cost': total_cost,
#     }
#     return render(request, 'checkout.html', context)


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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Order, OrderItem
from .forms import OrderItemUpdateForm

def order_details(request, order_id):
    """
    View to display and update details of a specific order.
    """
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    if request.method == 'POST':
        for item in order_items:
            form = OrderItemUpdateForm(request.POST, instance=item, prefix=f'item-{item.id}')
            if form.is_valid():
                form.save()
                messages.success(request, f"Order item {item.id} updated successfully!")
            else:
                messages.error(request, f"Failed to update order item {item.id}. Check your inputs.")
        return redirect('order_details', order_id=order_id)

    forms = [
        (item, OrderItemUpdateForm(instance=item, prefix=f'item-{item.id}'))
        for item in order_items
    ]

    return render(request, 'order_details.html', {'order': order, 'forms': forms})



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


from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Product

def manage_products(request):
    query = request.GET.get('q', '')  # Get search query from the URL
    products = Product.objects.all()

    # Filter products by description or number
    if query:
        products = products.filter(description__icontains=query) | products.filter(number__icontains=query)

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_quantity = request.POST.get('available_quantity')
        product = get_object_or_404(Product, id=product_id)
        product.available_quantity = new_quantity
        product.save()
        messages.success(request, f"Updated quantity for {product.description} to {new_quantity}.")
        return HttpResponseRedirect(reverse('manage_products'))  # Refresh the page

    return render(request, 'manage_products.html', {'products': products, 'query': query})

# from django.shortcuts import render, get_object_or_404, redirect
# from .models import Product
# from django.contrib import messages
#
# def manage_products(request):
#     # Filter products if search query is provided
#     search_query = request.GET.get('search', '')
#     products = Product.objects.all()
#     if search_query:
#         products = products.filter(
#             description__icontains=search_query
#         ) | products.filter(
#             number__icontains=search_query
#         )
#
#     return render(request, 'manage_products.html', {'products': products})
#
# def update_product_quantity(request, product_id):
#     if request.method == 'POST':
#         product = get_object_or_404(Product, id=product_id)
#         new_quantity = request.POST.get('available_quantity')
#         if new_quantity.isdigit() and int(new_quantity) >= 0:
#             product.available_quantity = int(new_quantity)
#             product.save()
#             messages.success(request, f"Updated quantity for {product.description}.")
#         else:
#             messages.error(request, "Invalid quantity.")
#     return redirect('manage_products')


def purchase_success(request):
    return render(request, 'purchase_success.html')

def purchase_failure(request):
    return render(request, 'purchase_failure.html')