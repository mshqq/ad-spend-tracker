from decimal import Decimal

import pytest

from campaigns.models import Campaign, Expense


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(
        username="owner", password="Test-password-54321"
    )


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        username="other", password="Test-password-54321"
    )


@pytest.fixture
def campaign(owner):
    return Campaign.objects.create(
        owner=owner, name="Поисковая реклама", budget=Decimal("1000.00")
    )


@pytest.fixture
def expense(campaign):
    return Expense.objects.create(campaign=campaign, amount=Decimal("125.50"))


@pytest.fixture
def owner_client(client, owner):
    client.force_login(owner)
    return client
