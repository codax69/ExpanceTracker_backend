"""
Django models for ExpenseIQ — migrated from Mongoose schemas.
Using SQLite as the database backend.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Expense category with optional monthly budget."""
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='ph-package')
    color = models.CharField(max_length=20, default='#10b981')
    monthly_budget = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return f"{self.icon} {self.name}"


class Expense(models.Model):
    """Individual expense transaction."""

    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Auto Pay', 'Auto Pay'),
        ('Other', 'Other'),
    ]

    RECURRING_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    category = models.CharField(max_length=100, db_index=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash'
    )
    notes = models.TextField(blank=True, default='')
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    expense_date = models.DateTimeField(db_index=True)
    is_recurring = models.BooleanField(default=False)
    recurring_type = models.CharField(
        max_length=10, choices=RECURRING_TYPE_CHOICES, blank=True, null=True
    )
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date']
        indexes = [
            models.Index(fields=['-expense_date', 'category']),
            models.Index(fields=['-expense_date', '-amount']),
            models.Index(fields=['category', '-expense_date']),
        ]

    def __str__(self):
        return f"{self.title} — ${self.amount}"


class Income(models.Model):
    """Income record."""

    PAYMENT_SOURCE_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('PayPal', 'PayPal'),
        ('Stripe', 'Stripe'),
        ('Cash', 'Cash'),
        ('Brokerage', 'Brokerage'),
        ('UPI', 'UPI'),
        ('Other', 'Other'),
    ]

    source = models.CharField(max_length=255, db_index=True)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True, default='')
    payment_source = models.CharField(
        max_length=20, choices=PAYMENT_SOURCE_CHOICES, default='Bank Transfer'
    )
    income_date = models.DateTimeField(db_index=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-income_date']
        indexes = [
            models.Index(fields=['-income_date']),
            models.Index(fields=['source', '-income_date']),
        ]

    def __str__(self):
        return f"{self.source} — ${self.amount}"


class Budget(models.Model):
    """Monthly budget settings."""
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.IntegerField()
    total_monthly_budget = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    warning_threshold = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Budget {self.month}/{self.year} — ${self.total_monthly_budget}"


class Report(models.Model):
    """Generated report metadata and summary."""

    REPORT_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
        ('financial_summary', 'Financial Summary'),
    ]
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    ]

    type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES, default='pdf')
    generated_file = models.CharField(max_length=500, blank=True, null=True)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    top_category = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.type} report ({self.start_date.date()} – {self.end_date.date()})"
