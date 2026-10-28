from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from .forms import CampaignForm, ExpenseForm
from .models import Campaign, Expense


class SignUpView(FormView):
    template_name = "registration/signup.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Аккаунт создан. Войдите с вашим логином и паролем.")
        return super().form_valid(form)


class OwnedCampaignMixin(LoginRequiredMixin):
    model = Campaign

    def get_queryset(self):
        return Campaign.objects.filter(owner=self.request.user).with_totals()


class CampaignListView(OwnedCampaignMixin, ListView):
    template_name = "campaigns/campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at", "-pk")


class CampaignCreateView(LoginRequiredMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"
    success_url = reverse_lazy("campaigns:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CampaignDetailView(OwnedCampaignMixin, DetailView):
    template_name = "campaigns/campaign_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = self.object.expenses.all()
        return context


class CampaignUpdateView(OwnedCampaignMixin, UpdateView):
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"

    def get_success_url(self):
        return reverse("campaigns:detail", kwargs={"pk": self.object.pk})


class CampaignDeleteView(OwnedCampaignMixin, DeleteView):
    template_name = "campaigns/campaign_confirm_delete.html"
    success_url = reverse_lazy("campaigns:list")


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "campaigns/expense_form.html"

    def get_campaign(self):
        return get_object_or_404(
            Campaign, pk=self.kwargs["campaign_pk"], owner=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.get_campaign()
        return context

    def form_valid(self, form):
        form.instance.campaign = self.get_campaign()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("campaigns:detail", kwargs={"pk": self.object.campaign_id})


class OwnedExpenseMixin(LoginRequiredMixin):
    model = Expense

    def get_queryset(self):
        return Expense.objects.filter(campaign__owner=self.request.user).select_related("campaign")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.object.campaign
        return context

    def get_success_url(self):
        return reverse("campaigns:detail", kwargs={"pk": self.object.campaign_id})


class ExpenseUpdateView(OwnedExpenseMixin, UpdateView):
    form_class = ExpenseForm
    template_name = "campaigns/expense_form.html"


class ExpenseDeleteView(OwnedExpenseMixin, DeleteView):
    template_name = "campaigns/expense_confirm_delete.html"
