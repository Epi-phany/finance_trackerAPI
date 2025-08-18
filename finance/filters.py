import django_filters
from .models import Transaction

class TransactionFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to   = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    choice_type = django_filters.CharFilter(field_name="choice_type")  # "INCOME" or "EXPENSE"
    category = django_filters.NumberFilter(field_name="category_id")

    class Meta:
        model = Transaction
        fields = ["choice_type", "category", "date_from", "date_to", "min_amount", "max_amount"]
