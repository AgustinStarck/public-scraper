from django import forms
from datetime import datetime

class EmpresaForm(forms.Form):
    empresas_manual = forms.CharField(
    label="ingresar empresas manualmente",
    required=False,
    widget=forms.Textarea(attrs={
        'placeholder': "Ingresa una empresa por línea\nEjemplo:\nGoogle\nAmazon\nMicrosoft",
        'rows': 3
    }),
    help_text="Separa cada empresa con un salto de línea"
)

    
    dias = forms.IntegerField(
        label="cantidad de dias",
        required=True,
        initial=0,
        help_text="Número de días para filtrar las noticias"
    )

class Analitica(forms.Form):
    Analiticas = forms.CharField(
        label="ingresar una búsqueda",
        required=False,
        widget=forms.TextInput(attrs={  
            'placeholder': "Ejemplo: Cafeterias",
            'class':"form-control form-control-sm rounded-start" ,
            'autocomplete': 'off'
        }),
        help_text="Ingresa tu búsqueda",
    )   