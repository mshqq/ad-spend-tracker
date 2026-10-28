from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class CampaignQuerySet(models.QuerySet):
    def with_totals(self):
        return self.annotate(
            total_spent=models.Sum("expenses__amount", default=Decimal("0.00")),
        ).annotate(
            remaining_budget=models.ExpressionWrapper(
                models.F("budget") - models.F("total_spent"),
                output_field=models.DecimalField(max_digits=18, decimal_places=2),
            ),
        )


class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ACTIVE = "active", "Активна"
        PAUSED = "paused", "Приостановлена"
        COMPLETED = "completed", "Завершена"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    name = models.CharField(max_length=255)
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CampaignQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(budget__gt=0),
                name="campaign_budget_positive",
            ),
        ]

    def __str__(self):
        return self.name


class Expense(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="expenses"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date = models.DateField(default=timezone.localdate)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="expense_amount_positive"
            ),
        ]

    def __str__(self):
        return f"{self.campaign}: {self.amount}"
