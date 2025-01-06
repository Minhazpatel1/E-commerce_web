from django import forms
from datetime import date

class CheckoutForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Shipping Address', 'rows': 3})
    )
    credit_card_number = forms.CharField(
        max_length=16,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Credit Card Number'}),
        help_text="Enter a valid 16-digit credit card number."
    )
    cvv = forms.CharField(
        max_length=3,
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'CVV'}),
        help_text="Enter the 3-digit CVV code."
    )
    expiration_date = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD',
                'type': 'date'
            }
        ),
        help_text="Enter the expiration date in YYYY-MM-DD format."
    )

    def clean_credit_card_number(self):
        cc_number = self.cleaned_data.get('credit_card_number')
        if not cc_number.isdigit() or len(cc_number) != 16:
            raise forms.ValidationError("Credit card number must be 16 digits.")
        return cc_number

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')
        if not cvv.isdigit() or len(cvv) != 3:
            raise forms.ValidationError("CVV must be a 3-digit number.")
        return cvv

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date < date.today():
            raise forms.ValidationError("Expiration date cannot be in the past.")
        return expiration_date

from django import forms
from .models import OrderItem

class OrderItemUpdateForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['shipping_label', 'invoice_label']
        widgets = {
            'shipping_label': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_label': forms.TextInput(attrs={'class': 'form-control'}),
        }
