from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Category(models.Model):
    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'
    
    CHOICES = [
        (INCOME,'Income'),
        (EXPENSE,'Expense'),
    ]
    
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='categories')
    name = models.CharField(max_length=50)
    choice_type = models.CharField(max_length=10,choices=CHOICES)
    
    class Meta:
        unique_together = ('user', 'name', 'choice_type')
        ordering = ['choice_type','name']
        
    def __str__(self):
        return f"{self.name} ({self.choice_type})"
    

class Transaction(models.Model):
    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
    choice_type = models.CharField(max_length=7, choices=Category.CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'choice_type']),
        ]
    def __str__(self):
        return f"{self.choice_type} {self.amount} on {self.date}"
    
class Budget(models.Model):
    PERIOD_MONTHLY = 'MONTH'
    PERIOD_YEARLY = 'YEAR'
    PERIOD_CHOICES = [
        (PERIOD_MONTHLY, 'Monthly'),
        (PERIOD_YEARLY, 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets', null=True, blank=True,
                                 help_text='If null, budget applies to ALL expense categories')
    period = models.CharField(max_length=5, choices=PERIOD_CHOICES, default=PERIOD_MONTHLY)
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    limit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'period', 'year', 'month'],
                name='unique_budget_per_period_and_category'
            )
        ]
        ordering = ['-year', '-month']

    def __str__(self):
        label = 'ALL' if self.category is None else self.category.name
        return f"{self.period} budget {self.year}-{self.year}-{self.month or ''}{label}:{self.limit}