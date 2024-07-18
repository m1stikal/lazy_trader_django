from django import forms
from .models import Stock, OpenPosition

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['code', 'name', 'exchange_prefix']

class OpenPositionForm(forms.ModelForm):
    class Meta:
        model = OpenPosition
        fields = ['stock', 'active', 'interval', 'period']