from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Part, CartItem, CustomUser
from django.utils import timezone
import pytz
import json
import uuid
import requests
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from .forms import CheckoutForm


# # Part Detail View
# def part_detail(request):
#     # Check if the user is logged in by validating the session
#     if not request.session.get('user_id'):
#         messages.error(request, "You need to log in first.")
#         return redirect('login')
#
#     # Fetch all parts from the database
#     parts = Part.objects.all()
#
#     # Get the current time in UTC
#     utc_time = timezone.now()
#
#     # Define the Chicago timezone using pytz
#     chicago_tz = pytz.timezone('America/Chicago')
#
#     # Convert UTC time to Chicago timezone
#     chicago_time = utc_time.astimezone(chicago_tz)
#
#     return render(request, 'part_detail.html', {
#         'parts': parts,             # Pass all parts to the template
#         'current_time': chicago_time,  # Pass the converted time to the template
#         'username': request.session.get('username'),  # Pass the logged-in user's username
#     })

from django.shortcuts import render
from .models import Part

def part_detail(request):
    # Fetch all parts from the legacy database
    parts = Part.objects.using('legacy').all()

    return render(request, 'part_detail.html', {
        'parts': parts,
    })


# Add to Cart View
def add_to_cart(request, part_id):
    # Ensure the user is logged in
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first to add items to the cart.")
        return redirect('login')

    # Fetch the part using the provided part ID
    part = get_object_or_404(Part, number=part_id)

    # Fetch the logged-in user
    user_id = request.session.get('user_id')
    user = get_object_or_404(CustomUser, id=user_id)

    # Check if the item is already in the cart for this user
    cart_item, created = CartItem.objects.get_or_create(part=part, user=user)
    if not created:
        # If the item is already in the cart, display a message
        messages.info(request, f"{part.description} is already in the cart!")
    else:
        # If the item is not in the cart, save it
        cart_item.save()
        messages.success(request, f"{part.description} was added to the cart.")

    return redirect('cart_detail')


# Cart Detail View
def cart_detail(request):
    # Ensure the user is logged in
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in to view the cart.")
        return redirect('login')

    # Fetch the logged-in user
    user_id = request.session.get('user_id')
    user = get_object_or_404(CustomUser, id=user_id)

    # Fetch cart items for the logged-in user
    cart_items = CartItem.objects.filter(user=user)
    total_price = sum(item.total_price for item in cart_items)

    return render(request, 'cart_detail.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


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


# Login View
# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#
#         try:
#             user = CustomUser.objects.get(username=username, password=password)
#             request.session['user_id'] = user.id
#             request.session['username'] = user.username
#             messages.success(request, f"Welcome, {user.name}!")
#             return redirect('part-detail')
#         except CustomUser.DoesNotExist:
#             messages.error(request, "Invalid credentials. Please register.")
#             return redirect('register')
#
#     return render(request, 'login.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser

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


# Checkout View
def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            name = "Minhaz Patel"
            credit_card_number = "6011123443211234"
            expiration_date = form.cleaned_data['expiration_date']
            amount = format(form.cleaned_data['amount'], '.2f')

            vendor_id = 'VE001-99'
            transaction_id = str(uuid.uuid4())

            data = {
                'vendor': vendor_id,
                'trans': transaction_id,
                'cc': credit_card_number,
                'name': name,
                'exp': expiration_date,
                'amount': amount,
            }

            url = 'http://blitz.cs.niu.edu/CreditCard/'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

            if response.status_code == 200:
                result = response.json()
                authorization_number = result.get('authorization')
                if authorization_number:
                    transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return JsonResponse({
                        'status': 'success',
                        'authorization_number': authorization_number,
                        'transaction_time': transaction_time,
                        'message': 'Payment authorized successfully!'
                    })
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to connect to the authorization service.'})

    return render(request, 'checkout.html', {'form': CheckoutForm()})


def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Use your name and Z-id for the cardholder name as required
            name = "Minhaz Patel, z1961329" # Replace with your name Ibrahin Al Azher, Z2006888 6011 1234 4321 1234
            credit_card_number = "6011123443211234"  # Replace with valid test card number
            expiration_date = form.cleaned_data['expiration_date']
            amount = format(form.cleaned_data['amount'], '.2f')

            # Generate unique vendor and transaction IDs
            vendor_id = 'VE001-99'
            transaction_id = str(uuid.uuid4())

            # Data payload for the authorization request
            data = {
                'vendor': vendor_id,
                'trans': transaction_id,
                'cc': credit_card_number,
                'name': name,
                'exp': expiration_date,
                'amount': amount,
            }

            # Send the POST request to the credit card authorization system
            url = 'http://blitz.cs.niu.edu/CreditCard/'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

            # Process the response
            print("API Response Status Code:", response.status_code)
            print("API Response JSON:", response.json())

            if response.status_code == 200:
                result = response.json()

                if 'errors' in result:
                    # Display the error message if there is an error
                    print("Error in transaction:", result['errors'])
                    return JsonResponse({'status': 'error', 'message': result['errors']})
                else:
                    authorization_number = result.get('authorization')
                    if authorization_number:
                        transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print("Authorization Code:", authorization_number)
                        print("Transaction Time:", transaction_time)
                        return JsonResponse({
                            'status': 'success',
                            'authorization_number': authorization_number,
                            'transaction_time': transaction_time,
                            'message': 'Payment authorized successfully!'
                        })
                    else:
                        print("Authorization number missing in response:", result)
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Authorization number missing in response',
                            'response': result
                        })
            else:
                print("Failed to connect. Status code:", response.status_code, "Response:", response.text)
                return JsonResponse({'status': 'error', 'message': 'Failed to connect to the authorization service.'})
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form})
