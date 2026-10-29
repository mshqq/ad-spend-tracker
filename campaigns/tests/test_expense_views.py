from datetime import date
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from campaigns.models import Campaign, Expense

pytestmark = pytest.mark.django_db


def expense_url(route, campaign, expense):
    pk = campaign.pk if route == "expense_create" else expense.pk
    return reverse(f"campaigns:{route}", args=[pk])


def payload(**overrides):
    return {"amount": "250.25", "date": "2026-10-20", "comment": "Реклама", **overrides}


@pytest.mark.parametrize("route", ["expense_create", "expense_update", "expense_delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_guests_cannot_access_expenses(client, campaign, expense, route, method):
    response = getattr(client, method)(expense_url(route, campaign, expense), payload())
    assert response.status_code == 302
    assert response.url.startswith(reverse("login") + "?next=")


@pytest.mark.parametrize("route", ["expense_create", "expense_update", "expense_delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_other_users_cannot_access_expenses(client, other_user, campaign, expense, route, method):
    client.force_login(other_user)
    response = getattr(client, method)(expense_url(route, campaign, expense), payload())
    assert response.status_code == 404
    expense.refresh_from_db()
    assert expense.amount == Decimal("125.50")
    assert Expense.objects.count() == 1


@pytest.mark.parametrize("route", ["expense_create", "expense_update", "expense_delete"])
def test_missing_objects_return_404(owner_client, route):
    assert owner_client.get(reverse(f"campaigns:{route}", args=[999999])).status_code == 404


def test_create_assigns_campaign_from_url(owner_client, campaign, other_user):
    foreign = Campaign.objects.create(owner=other_user, name="Foreign", budget=100)
    response = owner_client.post(reverse("campaigns:expense_create", args=[campaign.pk]), payload(campaign=foreign.pk))
    assert response.url == reverse("campaigns:detail", args=[campaign.pk])
    expense = Expense.objects.get()
    assert expense.campaign == campaign
    assert expense.amount == Decimal("250.25")
    assert expense.date == date(2026, 10, 20)


@pytest.mark.parametrize("invalid", [
    {"amount": "0"}, {"amount": "-1"}, {"amount": "1.001"},
    {"amount": "10000000000"}, {"date": "2026-02-30"}, {"date": "invalid"},
])
@pytest.mark.parametrize("route", ["expense_create", "expense_update"])
def test_invalid_expense_is_not_saved(owner_client, campaign, expense, route, invalid):
    response = owner_client.post(expense_url(route, campaign, expense), payload(**invalid))
    assert response.status_code == 200
    assert response.context["form"].errors
    assert Expense.objects.count() == 1
    expense.refresh_from_db()
    assert expense.amount == Decimal("125.50")


def test_owner_can_edit_without_moving_expense(owner_client, campaign, expense, other_user):
    foreign = Campaign.objects.create(owner=other_user, name="Foreign", budget=100)
    response = owner_client.post(reverse("campaigns:expense_update", args=[expense.pk]), payload(campaign=foreign.pk))
    assert response.url == reverse("campaigns:detail", args=[campaign.pk])
    expense.refresh_from_db()
    assert expense.campaign == campaign
    assert expense.amount == Decimal("250.25")
    assert expense.comment == "Реклама"


def test_owner_can_delete_only_by_post(owner_client, campaign, expense):
    address = reverse("campaigns:expense_delete", args=[expense.pk])
    assert owner_client.get(address).status_code == 200
    assert Expense.objects.filter(pk=expense.pk).exists()
    response = owner_client.post(address)
    assert response.url == reverse("campaigns:detail", args=[campaign.pk])
    assert not Expense.objects.filter(pk=expense.pk).exists()


def test_expense_mutations_require_csrf(owner, campaign, expense):
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    for route in ("expense_create", "expense_update", "expense_delete"):
        assert client.post(expense_url(route, campaign, expense), payload()).status_code == 403
    assert Expense.objects.count() == 1


def test_detail_shows_only_selected_campaign_expenses(owner_client, campaign, other_user, expense):
    foreign = Campaign.objects.create(owner=other_user, name="Foreign", budget=100)
    Expense.objects.create(campaign=foreign, amount=10, comment="Private expense")
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]))
    assert list(response.context["expenses"]) == [expense]
    assert "Private expense" not in response.content.decode()


def test_user_content_is_escaped(owner_client, campaign, expense):
    campaign.name = '<script>alert("campaign")</script>'
    campaign.save()
    expense.comment = '<script>alert("expense")</script>'
    expense.save()
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]))
    assert "<script>" not in response.content.decode()
    assert "&lt;script&gt;" in response.content.decode()
