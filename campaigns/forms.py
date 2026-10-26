from django import forms

from .models import Campaign, Expense


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "budget", "status"]
        labels = {"name": "Название", "budget": "Бюджет, ₽", "status": "Статус"}
        widgets = {"budget": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})}


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["amount", "date", "comment"]
        labels = {"amount": "Сумма, ₽", "date": "Дата", "comment": "Комментарий"}
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }
