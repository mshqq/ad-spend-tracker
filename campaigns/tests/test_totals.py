from decimal import Decimal

import pytest
from django.urls import reverse

from campaigns.models import Campaign, Expense

pytestmark = pytest.mark.django_db


def totals(campaign):
    return Campaign.objects.with_totals().get(pk=campaign.pk)


def test_empty_campaign(campaign):
    result = totals(campaign)
    assert result.total_spent == Decimal("0.00")
    assert result.remaining_budget == campaign.budget


def test_multiple_expenses_are_summed_exactly(campaign):
    for amount in ("0.10", "0.20", "125.50"):
        Expense.objects.create(campaign=campaign, amount=Decimal(amount))
    result = totals(campaign)
    assert result.total_spent == Decimal("125.80")
    assert result.remaining_budget == Decimal("874.20")


def test_totals_update_after_expense_edit_and_delete(campaign, expense):
    assert totals(campaign).remaining_budget == Decimal("874.50")
    expense.amount = Decimal("500.25")
    expense.save()
    assert totals(campaign).remaining_budget == Decimal("499.75")
    expense.delete()
    assert totals(campaign).remaining_budget == Decimal("1000.00")


def test_budget_edit_changes_remaining_amount(campaign, expense):
    campaign.budget = Decimal("200.00")
    campaign.save()
    assert totals(campaign).remaining_budget == Decimal("74.50")


@pytest.mark.parametrize("amount,warning", [("999.99", False), ("1000.00", False), ("1000.01", True)])
def test_over_budget_is_allowed_and_warned(owner_client, campaign, amount, warning):
    response = owner_client.post(reverse("campaigns:expense_create", args=[campaign.pk]), {
        "amount": amount, "date": "2026-10-20", "comment": "",
    })
    assert response.status_code == 302
    result = totals(campaign)
    assert result.remaining_budget == Decimal("1000.00") - Decimal(amount)
    for address in (reverse("campaigns:list"), reverse("campaigns:detail", args=[campaign.pk])):
        response = owner_client.get(address)
        assert ("Бюджет превышен" in response.content.decode()) is warning


def test_campaign_totals_are_isolated_and_use_one_query(owner, campaign, expense, django_assert_num_queries):
    second = Campaign.objects.create(owner=owner, name="Second", budget=500)
    Expense.objects.create(campaign=second, amount=50)
    with django_assert_num_queries(1):
        results = {row.pk: row for row in Campaign.objects.with_totals()}
    assert results[campaign.pk].total_spent == Decimal("125.50")
    assert results[second.pk].total_spent == Decimal("50.00")


def test_totals_recalculate_after_http_edit_and_delete(owner_client, campaign, expense):
    owner_client.post(reverse("campaigns:expense_update", args=[expense.pk]), {
        "amount": "300.00", "date": "2026-10-20", "comment": "",
    })
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]))
    assert response.context["campaign"].remaining_budget == Decimal("700.00")
    owner_client.post(reverse("campaigns:expense_delete", args=[expense.pk]))
    response = owner_client.get(reverse("campaigns:detail", args=[campaign.pk]))
    assert response.context["campaign"].remaining_budget == Decimal("1000.00")
