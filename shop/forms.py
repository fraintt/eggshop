from django import forms
from django.utils.translation import gettext_lazy as _


class OrderForm(forms.Form):
    packs = forms.IntegerField(
        min_value=1,
        initial=1,
        label=_("Number of packs (10 eggs each)"),
        widget=forms.NumberInput(attrs={"min": 1, "step": 1, "class": "input-number"}),
    )


class CancelOrderForm(forms.Form):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": _("Reason (optional)")}),
        label=_("Reason"),
    )
