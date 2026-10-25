from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from campaigns.models import Campaign, Expense

pytestmark = pytest.mark.django_db


def url(action, campaign):
    return reverse(f"campaigns:{action}", args=[campaign.pk])


def test_list_shows_only_own_campaigns(owner_client, owner, other_user, campaign):
    Campaign.objects.create(owner=other_user, name="Чужая кампания", budget=100)
    response = owner_client.get(reverse("campaigns:list"))
    assert response.status_code == 200
    assert list(response.context["campaigns"]) == [campaign]
    assert "Чужая кампания" not in response.content.decode()


def test_empty_list(owner_client):
    response = owner_client.get(reverse("campaigns:list"))
    assert "Кампаний пока нет" in response.content.decode()


@pytest.mark.parametrize("route", ["list", "create", "detail", "update", "delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_guests_are_redirected_to_login(client, campaign, route, method):
    address = reverse(f"campaigns:{route}") if route in ("list", "create") else url(route, campaign)
    response = getattr(client, method)(address)
    assert response.status_code == 302
    assert response.url.startswith(reverse("login") + "?next=")


@pytest.mark.parametrize("route", ["detail", "update", "delete"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_other_users_cannot_access_campaigns(client, other_user, campaign, route, method):
    client.force_login(other_user)
    response = getattr(client, method)(url(route, campaign), {"name": "Hacked", "budget": 1, "status": "active"})
    assert response.status_code == (405 if route == "detail" and method == "post" else 404)
    campaign.refresh_from_db()
    assert campaign.name == "Поисковая реклама"


@pytest.mark.parametrize("route", ["detail", "update", "delete"])
def test_missing_campaign_returns_404(owner_client, route):
    response = owner_client.get(reverse(f"campaigns:{route}", args=[999999]))
    assert response.status_code == 404


def test_owner_can_read_detail(owner_client, campaign):
    response = owner_client.get(url("detail", campaign))
    assert response.status_code == 200
    assert response.context["campaign"] == campaign


def test_create_ignores_submitted_owner(owner_client, owner, other_user):
    response = owner_client.post(reverse("campaigns:create"), {
        "name": "Новая кампания", "budget": "250.50", "status": "active", "owner": other_user.pk,
    })
    assert response.status_code == 302
    created = Campaign.objects.get()
    assert created.owner == owner
    assert created.budget == Decimal("250.50")
    assert created.status == Campaign.Status.ACTIVE


@pytest.mark.parametrize("budget,status", [("0", "draft"), ("-1", "draft"), ("1.001", "draft"), ("100", "invalid")])
def test_invalid_campaign_form_preserves_data(owner_client, campaign, budget, status):
    response = owner_client.post(url("update", campaign), {"name": "Changed", "budget": budget, "status": status})
    assert response.status_code == 200
    assert response.context["form"].errors
    campaign.refresh_from_db()
    assert campaign.budget == Decimal("1000.00")
    assert campaign.name == "Поисковая реклама"


def test_create_rejects_blank_name(owner_client):
    response = owner_client.post(reverse("campaigns:create"), {"name": "  ", "budget": 1, "status": "draft"})
    assert response.status_code == 200
    assert "name" in response.context["form"].errors
    assert not Campaign.objects.exists()


def test_owner_can_update_without_changing_owner(owner_client, campaign, other_user):
    original_owner = campaign.owner_id
    response = owner_client.post(url("update", campaign), {
        "name": "Обновлённая кампания", "budget": "300.00", "status": "paused", "owner": other_user.pk,
    })
    assert response.url == url("detail", campaign)
    campaign.refresh_from_db()
    assert campaign.name == "Обновлённая кампания"
    assert campaign.owner_id == original_owner


def test_deletion_requires_post_and_removes_expenses(owner_client, campaign, expense):
    response = owner_client.get(url("delete", campaign))
    assert response.status_code == 200
    assert Campaign.objects.filter(pk=campaign.pk).exists()
    response = owner_client.post(url("delete", campaign))
    assert response.url == reverse("campaigns:list")
    assert not Campaign.objects.filter(pk=campaign.pk).exists()
    assert not Expense.objects.filter(pk=expense.pk).exists()


def test_campaign_post_requires_csrf(owner, campaign):
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    assert client.post(url("delete", campaign)).status_code == 403
    assert Campaign.objects.filter(pk=campaign.pk).exists()
