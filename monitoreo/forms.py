from django import forms
from .models import Proyecto

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'codigo_medidor', 'marca', 'ubicacion', 'activo', 'latitud', 'longitud', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'codigo_medidor': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'marca': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'ubicacion': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'activo': forms.CheckboxInput(attrs={'class': 'rounded'}),
            'latitud': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'step': 'any'}),
            'longitud': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'step': 'any'}),
            'direccion': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
        }