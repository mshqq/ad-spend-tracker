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


class CampaignFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[("", "Все статусы"), *Campaign.Status.choices],
    )


class ExpenseFilterForm(forms.Form):
    date_from = forms.DateField(
        label="Дата с", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label="Дата по", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )

    def clean(self):
        data = super().clean()
        date_from, date_to = data.get("date_from"), data.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Дата начала должна быть не позже даты окончания.")
        return data
