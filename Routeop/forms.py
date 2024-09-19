from django import forms

class RouteForm(forms.Form):
    start_stop = forms.CharField(label='Start Bus Stop', max_length=100)
    end_stop = forms.CharField(label='End Bus Stop', max_length=100)
