from django.shortcuts import render, redirect, get_object_or_404
from .models import Part, CartItem
from django.utils import timezone
import pytz

# import json
# import uuid
# import requests
# from django.shortcuts import render, redirect
# from django.http import JsonResponse
# from .forms import CheckoutForm

def part_detail(request):
    # Fetch all parts from the database
    parts = Part.objects.all()

    # Get the current time in UTC
    utc_time = timezone.now()

    # Define the Chicago timezone using pytz
    chicago_tz = pytz.timezone('America/Chicago')

    # Convert UTC time to Chicago timezone
    chicago_time = utc_time.astimezone(chicago_tz)

    return render(request, 'part_detail.html', {
        'parts': parts,             # Pass all parts to the template
        'current_time': chicago_time  # Pass the converted time to the template
    })

def add_to_cart(request, part_id):
    part = get_object_or_404(Part, number=part_id)  # Using 'number' as the identifier
    cart_item, created = CartItem.objects.get_or_create(part=part)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_detail')

def cart_detail(request):
    cart_items = CartItem.objects.all()
    total_price = sum(item.total_price for item in cart_items)
    return render(request, 'cart_detail.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

import json
import uuid
import requests
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from .forms import CheckoutForm

def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Use your name and Z-id for the cardholder name as required
            name = "Minhaz Patel Z1961329"
            credit_card_number = form.cleaned_data['credit_card_number']
            expiration_date = form.cleaned_data['expiration_date']
            amount = form.cleaned_data['amount']

            # Generate unique vendor and transaction IDs
            vendor_id = 'VE001-99'  # Fixed vendor ID
            transaction_id = str(uuid.uuid4())  # Generate a unique transaction ID

            # Prepare the data payload for the authorization request
            data = {
                'vendor': vendor_id,
                'trans': transaction_id,
                'cc': credit_card_number,
                'name': name,
                'exp': expiration_date,
                'amount': str(amount),
            }

            # Send the POST request to the credit card authorization system
            url = 'http://blitz.cs.niu.edu/CreditCard/'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))

            # Process the response
            if response.status_code == 200:
                result = response.json()
                if 'Error' in result:
                    # Log the error for debugging purposes
                    print("Error in transaction:", result)
                    return JsonResponse({'status': 'error', 'message': result})
                else:
                    # Successful authorization - capture the authorization number and timestamp
                    authorization_number = result.get('authorization')
                    transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Log the date and time of the transaction and authorization code
                    print("Transaction Successful!")
                    print("Date and Time of Transaction:", transaction_time)
                    print("Authorization Code:", authorization_number)

                    # Return the authorization details in the response
                    return JsonResponse({
                        'status': 'success',
                        'authorization_number': authorization_number,
                        'transaction_time': transaction_time,
                        'message': 'Payment authorized successfully!'
                    })
            else:
                # Log the entire response if status code is not 200
                print("Failed to connect. Status code:", response.status_code, "Response:", response.text)
                return JsonResponse({'status': 'error', 'message': 'Failed to connect to the authorization service.'})
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form})
