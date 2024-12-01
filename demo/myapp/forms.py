# forms.py
from django import forms

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, label="Cardholder Name")
    credit_card_number = forms.CharField(max_length=16, label="Credit Card Number")
    expiration_date = forms.CharField(max_length=7, label="Expiration Date")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")
