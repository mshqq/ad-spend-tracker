from django import forms

from .models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "budget", "status"]
        labels = {"name": "Название", "budget": "Бюджет, ₽", "status": "Статус"}
        widgets = {"budget": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})}
