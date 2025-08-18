from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TransactionViewSet, BudgetViewSet, ReportsView, DashboardView

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"budgets", BudgetViewSet, basename="budget")

urlpatterns = [
    path("", include(router.urls)),
    path("summary/", ReportsView.as_view(), name="reports-summary"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
