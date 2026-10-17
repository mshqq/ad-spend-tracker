from django.contrib import admin

from .models import Campaign, Expense


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "budget", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "owner__username"]
    list_select_related = ["owner"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["campaign", "amount", "date", "comment"]
    list_filter = ["date", "campaign__status"]
    search_fields = ["campaign__name", "comment"]
    list_select_related = ["campaign"]
    autocomplete_fields = ["campaign"]
