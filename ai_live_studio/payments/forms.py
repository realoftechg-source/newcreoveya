from django import forms

from payments.models import PaymentSubmission

MAX_RECEIPT_SIZE_MB = 8
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


class PaymentSubmissionForm(forms.ModelForm):
    class Meta:
        model = PaymentSubmission
        fields = ['plan', 'method', 'receipt']
        widgets = {
            'plan': forms.HiddenInput(),
            'method': forms.HiddenInput(),
            'receipt': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
        }

    def clean_receipt(self):
        receipt = self.cleaned_data['receipt']
        content_type = getattr(receipt, 'content_type', None)
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError('Please upload a JPEG, PNG, or WEBP image of your receipt.')
        if receipt.size > MAX_RECEIPT_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(f'Receipt image must be under {MAX_RECEIPT_SIZE_MB}MB.')
        return receipt
