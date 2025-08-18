from datetime import date
from calendar import monthrange
from decimal import Decimal

from django.db.models import Sum, Q, F
from django.utils.timezone import now

from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Transaction, Budget
from .serializers import CategorySerializer, TransactionSerializer, BudgetSerializer
from .permissions import IsOwner
from .filters import TransactionFilter


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        # Prevent deleting categories in use (optional; remove to allow cascading via PROTECT)
        if instance.transactions.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete category that has transactions.")
        return super().perform_destroy(instance)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filterset_class = TransactionFilter
    search_fields = ["description"]
    ordering_fields = ["date", "amount", "created_at"]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = Budget.objects.filter(user=self.request.user)
        # Annotate utilization
        def monthly_q(year, month, category_id):
            base = Q(user=self.request.user, date__year=year, type=Category.EXPENSE)
            if month:
                base &= Q(date__month=month)
            if category_id:
                base &= Q(category_id=category_id)
            return base

        # We can't annotate with per-row dynamic queries easily without Subquery + OuterRef;
        # compute on the fly in list/retrieve actions below for accuracy.
        return qs

    def list(self, request, *args, **kwargs):
        data = []
        for b in self.get_queryset().select_related("category"):
            utilized = self._utilized_for_budget(b)
            remaining = (b.limit - utilized) if b.limit is not None else Decimal("0.00")
            item = BudgetSerializer(b, context={"request": request}).data
            item["utilized"] = f"{utilized:.2f}"
            item["remaining"] = f"{remaining:.2f}"
            data.append(item)
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        b = self.get_object()
        utilized = self._utilized_for_budget(b)
        remaining = (b.limit - utilized) if b.limit is not None else Decimal("0.00")
        payload = BudgetSerializer(b, context={"request": request}).data
        payload["utilized"] = f"{utilized:.2f}"
        payload["remaining"] = f"{remaining:.2f}"
        return Response(payload)

    @staticmethod
    def _utilized_for_budget(budget: Budget) -> Decimal:
        filters = dict(user_id=budget.user_id, choice_type=Category.EXPENSE, date__year=budget.year)
        if budget.period == Budget.PERIOD_MONTHLY:
            filters["date__month"] = budget.month
        if budget.category_id:
            filters["category_id"] = budget.category_id
        agg = Transaction.objects.filter(**filters).aggregate(total=Sum("amount"))
        return agg["total"] or Decimal("0.00")


class ReportsView(APIView):
    """
    GET /api/reports/summary/?year=2025&month=8  -> monthly
    GET /api/reports/summary/?year=2025          -> yearly
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        year = int(request.query_params.get("year", now().year))
        month = request.query_params.get("month")
        month = int(month) if month else None

        tx_qs = Transaction.objects.filter(user=user, date__year=year)
        if month:
            tx_qs = tx_qs.filter(date__month=month)

        totals = tx_qs.values("choice_type").annotate(total=Sum("amount"))
        total_income = next((t["total"] for t in totals if t["choice_type"] == Category.INCOME), 0) or 0
        total_expense = next((t["total"] for t in totals if t["choice_type"] == Category.EXPENSE), 0) or 0
        balance = (total_income or 0) - (total_expense or 0)

        by_category = (
            tx_qs.values("category__id", "category__name", "choice_type")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        # Budget utilization snapshot (only for matching period)
        budgets = Budget.objects.filter(user=user, year=year)
        if month:
            budgets = budgets.filter(Q(period=Budget.PERIOD_MONTHLY, month=month) | Q(period=Budget.PERIOD_YEARLY))
        else:
            budgets = budgets.filter(period=Budget.PERIOD_YEARLY)

        budget_items = []
        for b in budgets.select_related("category"):
            utilized = BudgetViewSet._utilized_for_budget(b)
            remaining = (b.limit - utilized) if b.limit is not None else None
            budget_items.append({
                "id": b.id,
                "category": b.category.name if b.category else None,
                "period": b.period,
                "year": b.year,
                "month": b.month,
                "limit": float(b.limit),
                "utilized": float(utilized),
                "remaining": float(remaining) if remaining is not None else None,
            })

        return Response({
            "period": {"year": year, "month": month},
            "totals": {
                "income": float(total_income or 0),
                "expense": float(total_expense or 0),
                "balance": float(balance or 0),
            },
            "by_category": list(by_category),
            "budgets": budget_items,
        })


class DashboardView(APIView):
    """
    Quick snapshot for current month.
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        today = date.today()
        year, month = today.year, today.month
        qs = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)
        totals = qs.values("choice_type").annotate(total=Sum("amount"))
        income = next((t["total"] for t in totals if t["choice_type"] == Category.INCOME), 0) or 0
        expense = next((t["total"] for t in totals if t["choice_type"] == Category.EXPENSE), 0) or 0
        start, end = date(year, month, 1), date(year, month, monthrange(year, month)[1])
        return Response({
            "period": {"start": str(start), "end": str(end)},
            "income": float(income), "expense": float(expense),
            "balance": float((income or 0) - (expense or 0)),
            "transactions_count": qs.count(),
        })
