from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Chọn file CSV")