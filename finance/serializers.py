from rest_framework import serializers
from django.db.models import Sum
from .models import Category, Transaction, Budget

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "choice_type", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "category", "choice_type", "amount", "description", "date", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        category = attrs.get("category")
        ttype = attrs.get("choice_type")
        amount = attrs.get("amount")
        if category and category.user != user:
            raise serializers.ValidationError("Category does not belong to you.")
        if category and ttype and category.choice_type != ttype:
            raise serializers.ValidationError("Transaction type must match category type.")
        if amount is not None and amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class BudgetSerializer(serializers.ModelSerializer):
    utilized = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "category", "period", "year", "month", "limit", "utilized", "remaining", "created_at"]
        read_only_fields = ["id", "created_at", "utilized", "remaining"]

    def validate(self, attrs):
        user = self.context["request"].user
        category = attrs.get("category")
        period = attrs.get("period")
        month = attrs.get("month")
        limit = attrs.get("limit")

        if category and category.user != user:
            raise serializers.ValidationError("Category does not belong to you.")

        if period == Budget.MONTHLY and not month:
            raise serializers.ValidationError("Month is required for monthly budgets.")
        if period == Budget.YEARLY and month:
            raise serializers.ValidationError("Month must be empty for yearly budgets.")
        if limit is not None and limit <= 0:
            raise serializers.ValidationError("Budget limit must be greater than zero.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    