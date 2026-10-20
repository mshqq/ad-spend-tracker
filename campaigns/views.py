from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from .models import Campaign


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
        return Campaign.objects.filter(owner=self.request.user)


class CampaignListView(OwnedCampaignMixin, ListView):
    template_name = "campaigns/campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at", "-pk")
