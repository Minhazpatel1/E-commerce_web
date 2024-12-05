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
    Add a part to the cart, decreasing available_quantity.
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
        part.available_quantity -= 1  # Decrease available quantity
        part.save()
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

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

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
            )

            # Create order items and update available quantities
            for item in cart_items:
                product = item.part
                if product.available_quantity >= item.quantity:
                    product.available_quantity -= item.quantity
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






# def purchase(request):
#     if request.method == 'POST':
#         # Generate a unique identifier, or use another method to ensure uniqueness
#         unique_transaction_id = uuid.uuid4().hex  # Example using UUID
#
#         # Create a new Transaction entry directly
#         Transaction.objects.create(
#             id=unique_transaction_id,  # Using the generated UUID as the transaction ID
#             cc=request.POST.get('creditCard'),
#             exp=request.POST.get('creditCardExpirationDate'),
#             name=request.POST.get('name'),  # Assuming these fields are provided in the form
#             vendor="Default Vendor",  # Default or derived value
#             trans="New Purchase",  # Example transaction description
#             amount=request.POST.get('amount', 0.00),  # Assuming amount is provided, defaulting to 0.00 if not
#             brand="Default Brand",  # Default or derived value
#             authorization="Authorized",  # Default or specific logic to set this field
#             timeStamp=int(time.time())  # Example to set current timestamp
#         )
#         messages.success(request, 'Transaction entry created successfully with ID: ' + unique_transaction_id)
#         return redirect('purchase_success')  # Redirect to a success page
#     else:
#         messages.error(request, 'Invalid request method.')
#         # return redirect('part-detail', product_id=part_id)
#         return redirect('purchase_success')

def purchase_success(request):
    return render(request, 'purchase_success.html')

def purchase_failure(request):
    return render(request, 'purchase_failure.html')

# def checkout(request):
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Get logged-in user
#             user_id = request.session.get('user_id')
#             if not user_id:
#                 messages.error(request, "You need to log in to proceed with checkout.")
#                 return redirect('login')
#
#             user = get_object_or_404(CustomUser, id=user_id)
#
#             # Retrieve cart items for the user
#             cart_items = CartItem.objects.filter(user=user)
#             if not cart_items.exists():
#                 messages.error(request, "Your cart is empty.")
#                 return redirect('cart_detail')
#
#             # Calculate total amount and shipping
#             total_weight = sum(item.part.weight * item.quantity for item in cart_items)
#             shipping_handling = Decimal('10') + (Decimal(total_weight) * Decimal('0.5'))  # Ensure consistent use of Decimal
#             total_amount = sum(item.total_price for item in cart_items) + shipping_handling
#
#             # Simulate payment authorization
#             payment_data = {
#                 "vendor": "VE001-99",
#                 "trans": str(uuid.uuid4()),
#                 "cc": form.cleaned_data['credit_card_number'],
#                 "name": user.name,
#                 "exp": form.cleaned_data['expiration_date'].strftime("%Y-%m"),
#                 "amount": f"{total_amount:.2f}",
#             }
#             url = "http://blitz.cs.niu.edu/CreditCard/"
#             headers = {"Content-Type": "application/json"}
#             try:
#                 response = requests.post(url, headers=headers, data=json.dumps(payment_data))
#                 response.raise_for_status()
#                 result = response.json()
#
#                 if 'authorization' in result:
#                     # Create an order
#                     order = Order.objects.create(
#                         customer_name=user.name,
#                         customer_email=user.email,
#                         customer_address=form.cleaned_data['address'],
#                         total_amount=total_amount,
#                         shipping_handling=shipping_handling,
#                         order_number=str(uuid.uuid4()),  # Generate unique order number
#                     )
#
#                     # Create order items and update product quantities
#                     for item in cart_items:
#                         product = item.part
#                         OrderItem.objects.create(
#                             order=order,
#                             product=product,
#                             quantity=item.quantity,
#                             total_price=item.total_price
#                         )
#                         # Reduce available quantity
#                         product.available_quantity -= item.quantity
#                         if product.available_quantity < 0:
#                             messages.error(request, f"Insufficient stock for {product.description}.")
#                             return redirect('cart_detail')
#                         product.save()
#
#                     # Clear the cart for this user
#                     cart_items.delete()
#
#                     # Display success message
#                     messages.success(request, f"Order {order.order_number} placed successfully!")
#
#                     # Optional: Send email confirmation
#                     # send_order_confirmation_email(order)
#
#                     return redirect('part_detail')
#                 else:
#                     messages.error(request, "Payment authorization failed. Please try again.")
#             except requests.RequestException:
#                 messages.error(request, "Failed to connect to the payment gateway. Please try again.")
#         else:
#             messages.error(request, "Invalid form data. Please correct the errors.")
#     else:
#         form = CheckoutForm()
#
#     return render(request, 'checkout.html', {'form': form})


# def checkout(request):
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Collect form data
#             name = "minhaz patel"
#             # form.cleaned_data['name']
#             email = "ptlminhaz123@gmail.com"
#             #form.cleaned_data['email']
#             address = "home center"
#             # form.cleaned_data['address']
#             credit_card_number = "6011123443211234"
#             # form.cleaned_data['credit_card_number']
#             cvv = "123"
#             # form.cleaned_data['cvv']
#             expiration_date = "12/12/2025"
#             # form.cleaned_data['expiration_date']
#
#             # Retrieve cart items from session
#             cart_items = request.session.get('cart', [])
#             if not cart_items:
#                 messages.error(request, "Your cart is empty.")
#                 return redirect('cart_detail')
#
#             # Calculate total amount and shipping
#             total_weight = sum(item['weight'] * item['quantity'] for item in cart_items)
#             shipping_handling = 10 + (total_weight * 0.5)  # Example calculation
#             total_amount = sum(item['price'] * item['quantity'] for item in cart_items) + shipping_handling
#
#             # Simulate payment authorization
#             payment_data = {
#                 "vendor": "VE001-99",
#                 "trans": str(uuid.uuid4()),
#                 "cc": credit_card_number,
#                 "name": name,
#                 "exp": expiration_date.strftime("%Y-%m"),
#                 "amount": f"{total_amount:.2f}",
#             }
#             url = "http://blitz.cs.niu.edu/CreditCard/"
#             headers = {"Content-Type": "application/json"}
#             try:
#                 response = requests.post(url, headers=headers, data=json.dumps(payment_data))
#                 response.raise_for_status()  # Ensure we handle non-200 statuses
#                 result = response.json()
#
#                 if 'authorization' in result:
#                     # Create an order
#                     order = Order.objects.create(
#                         customer_name=name,
#                         customer_email=email,
#                         customer_address=address,
#                         total_amount=total_amount,
#                         shipping_handling=shipping_handling,
#                         order_number=str(uuid.uuid4()),  # Generate unique order number
#                     )
#
#                     # Create order items and update product quantities
#                     for item in cart_items:
#                         product = get_object_or_404(Product, number=item['id'])
#                         OrderItem.objects.create(
#                             order=order,
#                             product=product,
#                             quantity=item['quantity'],
#                             total_price=item['price'] * item['quantity']
#                         )
#                         # Update product quantity
#                         product.quantity -= item['quantity']
#                         if product.quantity < 0:
#                             messages.error(request, f"Insufficient stock for {product.description}.")
#                             return redirect('cart_detail')
#                         product.save()
#
#                     # Clear the cart
#                     request.session['cart'] = []
#
#                     # Display success message
#                     messages.success(request, f"Order {order.order_number} placed successfully!")
#
#                     # Optional: Send email confirmation
#                     # send_order_confirmation_email(order)
#
#                     return redirect('part_detail')
#                 else:
#                     messages.error(request, "Payment authorization failed. Please try again.")
#             except requests.RequestException as e:
#                 messages.error(request, "Failed to connect to the payment gateway. Please try again.")
#         else:
#             messages.error(request, "Invalid form data. Please correct the errors.")
#     else:
#         form = CheckoutForm()
#
#     return render(request, 'checkout.html', {'form': form})



# def checkout(request):
#     if request.method == 'POST':
#         form = CheckoutForm(request.POST)
#         if form.is_valid():
#             # Get cart items for the user
#             user_id = request.session.get('user_id')
#             user = get_object_or_404(CustomUser, id=user_id)
#             cart_items = CartItem.objects.filter(user=user)
#
#             # Compute total amount and shipping/handling charges
#             total_weight = sum(item.part.weight * item.quantity for item in cart_items)
#             total_amount = sum(item.total_price for item in cart_items)
#             shipping_handling = 10 + (0.05 * total_weight)  # Example: $10 base + $0.05 per kg
#             final_amount = total_amount + shipping_handling
#
#             # Simulate credit card processing
#             name = f"{user.name}"
#             credit_card_number = form.cleaned_data['credit_card_number']
#             expiration_date = form.cleaned_data['expiration_date']
#
#             # Generate unique vendor and transaction IDs
#             vendor_id = 'VE001-99'
#             transaction_id = str(uuid.uuid4())
#
#             # Data payload for the authorization request
#             data = {
#                 'vendor': vendor_id,
#                 'trans': transaction_id,
#                 'cc': credit_card_number,
#                 'name': name,
#                 'exp': expiration_date,
#                 'amount': final_amount,
#             }
#
#             url = 'http://blitz.cs.niu.edu/CreditCard/'
#             headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
#             response = requests.post(url, headers=headers, data=json.dumps(data))
#
#             if response.status_code == 200:
#                 result = response.json()
#                 if result.get('authorization'):
#                     # Create the Order
#                     order = Order.objects.create(
#                         customer=user,
#                         total_amount=total_amount,
#                         shipping_handling=shipping_handling,
#                         final_amount=final_amount,
#                         status='Authorized'
#                     )
#
#                     # Add items to the order and update the Product quantities
#                     for item in cart_items:
#                         # Deduct the quantity from the product
#                         product = Product.objects.get(number=item.part.number)
#                         if product.available_quantity >= item.quantity:
#                             product.available_quantity -= item.quantity
#                             product.save()
#
#                             # Add the item to the order
#                             OrderItem.objects.create(
#                                 order=order,
#                                 product=product,
#                                 quantity=item.quantity,
#                                 price=product.price
#                             )
#                         else:
#                             messages.error(request, f"Not enough stock for {product.description}.")
#                             return redirect('cart_detail')
#
#                     # Clear the cart
#                     cart_items.delete()
#
#                     # Send confirmation email
#                     send_mail(
#                         'Order Confirmation',
#                         f"Your order {order.order_number} has been placed successfully.\n"
#                         f"Total Amount: ${final_amount:.2f}\n"
#                         f"Shipping and Handling: ${shipping_handling:.2f}",
#                         settings.DEFAULT_FROM_EMAIL,
#                         [user.email],
#                         fail_silently=False,
#                     )
#
#                     messages.success(request, "Order placed successfully!")
#                     return redirect('part-detail')
#                 else:
#                     messages.error(request, "Payment authorization failed.")
#             else:
#                 messages.error(request, "Failed to connect to the payment gateway.")
#
#     else:
#         form = CheckoutForm()
#
#     return render(request, 'checkout.html', {'form': form})