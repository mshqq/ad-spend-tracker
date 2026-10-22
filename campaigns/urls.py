from django.urls import path

from . import views

app_name = "campaigns"

urlpatterns = [
    path("", views.CampaignListView.as_view(), name="list"),
    path("campaigns/new/", views.CampaignCreateView.as_view(), name="create"),
    path("campaigns/<int:pk>/", views.CampaignDetailView.as_view(), name="detail"),
]
