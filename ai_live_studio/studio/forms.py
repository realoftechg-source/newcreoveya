from django import forms

from studio.models import Look

MAX_LOOK_IMAGE_SIZE_MB = 8
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


class LookUploadForm(forms.ModelForm):
    name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. "John" or "Business Look"'})
    )
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'})
    )

    class Meta:
        model = Look
        fields = ['name', 'image']

    def clean_image(self):
        image = self.cleaned_data['image']

        content_type = getattr(image, 'content_type', None)
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError('Please upload a JPEG, PNG, or WEBP image.')

        if image.size > MAX_LOOK_IMAGE_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(f'Image must be under {MAX_LOOK_IMAGE_SIZE_MB}MB.')

        return image
