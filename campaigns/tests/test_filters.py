from decimal import Decimal

import pytest
from django.urls import reverse

from campaigns.models import Campaign, Expense

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("status", Campaign.Status.values)
def test_status_filter(owner_client, owner, other_user, status):
    own = [Campaign.objects.create(owner=owner, name=value, budget=100, status=value) for value in Campaign.Status.values]
    Campaign.objects.create(owner=other_user, name="Foreign", budget=100, status=status)
    response = owner_client.get(reverse("campaigns:list"), {"status": status})
    assert list(response.context["campaigns"]) == [row for row in own if row.status == status]


def test_blank_status_shows_all_campaigns(owner_client, campaign):
    response = owner_client.get(reverse("campaigns:list"), {"status": ""})
    assert list(response.context["campaigns"]) == [campaign]


def test_invalid_status_shows_error(owner_client, campaign):
    response = owner_client.get(reverse("campaigns:list"), {"status": "invalid"})
    assert response.status_code == 200
    assert "status" in response.context["filter_form"].errors
    assert not response.context["campaigns"].exists()


@pytest.mark.parametrize("params,expected_dates", [
    ({}, ["2026-10-21", "2026-10-20", "2026-10-19"]),
    ({"date_from": "2026-10-20"}, ["2026-10-21", "2026-10-20"]),
    ({"date_to": "2026-10-20"}, ["2026-10-20", "2026-10-19"]),
    ({"date_from": "2026-10-20", "date_to": "2026-10-20"}, ["2026-10-20"]),
    ({"date_from": "2026-10-22"}, []),
])
def test_date_filter_includes_boundaries_without_changing_totals(owner_client, campaign, params, expected_dates):
    for day in ("2026-10-19", "2026-10-20", "2026-10-21"):
        Expense.objects.create(campaign=campaign, amount=Decimal("10.25"), date=day)
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]), params)
    assert response.status_code == 200
    assert [row.date.isoformat() for row in response.context["expenses"]] == expected_dates
    assert response.context["campaign"].total_spent == Decimal("30.75")
    assert response.context["campaign"].remaining_budget == Decimal("969.25")


@pytest.mark.parametrize("params,error_field", [
    ({"date_from": "bad"}, "date_from"),
    ({"date_to": "2026-02-30"}, "date_to"),
    ({"date_from": "2026-10-21", "date_to": "2026-10-20"}, "__all__"),
])
def test_invalid_dates_show_errors(owner_client, campaign, expense, params, error_field):
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]), params)
    assert response.status_code == 200
    assert error_field in response.context["filter_form"].errors
    assert not response.context["expenses"].exists()
    assert response.context["campaign"].total_spent == expense.amount


def test_filters_do_not_allow_access_to_foreign_campaign(client, other_user, campaign):
    client.force_login(other_user)
    response = client.get(reverse("campaigns:detail", args=[campaign.pk]), {"date_from": "2026-10-20"})
    assert response.status_code == 404
