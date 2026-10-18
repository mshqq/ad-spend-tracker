from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from campaigns.models import Campaign, Expense

pytestmark = pytest.mark.django_db


def test_campaign_defaults_and_owner_relation(campaign, owner):
    campaign.full_clean()
    assert campaign.status == Campaign.Status.DRAFT
    assert campaign.created_at is not None
    assert owner.campaigns.get() == campaign
    assert str(campaign) == campaign.name


def test_expense_defaults_and_campaign_relation(expense, campaign):
    expense.full_clean()
    assert expense.date == timezone.localdate()
    assert expense.comment == ""
    assert campaign.expenses.get() == expense


@pytest.mark.parametrize("amount", ["0.00", "-0.01"])
@pytest.mark.parametrize("model,field", [(Campaign, "budget"), (Expense, "amount")])
def test_positive_money_validation(model, field, amount, owner, campaign):
    fields = {"owner": owner, "name": "Test"} if model is Campaign else {"campaign": campaign}
    instance = model(**fields, **{field: Decimal(amount)})
    with pytest.raises(ValidationError) as error:
        instance.full_clean()
    assert field in error.value.message_dict
    with pytest.raises(IntegrityError), transaction.atomic():
        instance.save()


@pytest.mark.parametrize("amount", ["0.01", "9999999999.99"])
def test_money_boundaries(owner, campaign, amount):
    Campaign(owner=owner, name="Test", budget=Decimal(amount)).full_clean()
    Expense(campaign=campaign, amount=Decimal(amount)).full_clean()


@pytest.mark.parametrize("amount", ["1.001", "10000000000.00"])
def test_invalid_money_precision(campaign, amount):
    with pytest.raises(ValidationError):
        Expense(campaign=campaign, amount=Decimal(amount)).full_clean()


def test_campaign_rejects_unknown_status(campaign):
    campaign.status = "unknown"
    with pytest.raises(ValidationError) as error:
        campaign.full_clean()
    assert "status" in error.value.message_dict


def test_deleting_campaign_deletes_its_expenses(expense, campaign):
    campaign.delete()
    assert not Expense.objects.filter(pk=expense.pk).exists()


def test_deleting_owner_deletes_campaign_and_expenses(owner, campaign, expense):
    owner.delete()
    assert not Campaign.objects.filter(pk=campaign.pk).exists()
    assert not Expense.objects.filter(pk=expense.pk).exists()
