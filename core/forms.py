"""
Forms per Ericsson Analyzer
"""
from django import forms
from .models import LogFile


class LogFileUploadForm(forms.ModelForm):
    """Form per upload file log"""
    
    class Meta:
        model = LogFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.txt,.log',
                'id': 'fileInput'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError("Nessun file selezionato")
        
        # Verifica estensione
        if not file.name.endswith(('.txt', '.log')):
            raise forms.ValidationError("Solo file .txt o .log sono accettati")
        
        # Verifica dimensione (max 50MB)
        if file.size > 50 * 1024 * 1024:
            raise forms.ValidationError("File troppo grande (max 50MB)")
        
        return file
