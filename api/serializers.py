"""
Serializers for ExpenseIQ API — matching the Node.js request/response format.
"""
from rest_framework import serializers
from .models import Expense, Income, Category, Budget, Report


# ───── Category Serializer ─────
class CategorySerializer(serializers.ModelSerializer):
    monthlyBudget = serializers.DecimalField(
        source='monthly_budget', max_digits=12, decimal_places=2, required=False
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'monthlyBudget', 'createdAt', 'updatedAt']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['monthlyBudget'] = float(ret.get('monthlyBudget', 0) or 0)
        return ret


# ───── Expense Serializer ─────
class ExpenseSerializer(serializers.ModelSerializer):
    paymentMethod = serializers.CharField(source='payment_method', required=False)
    receiptImage = serializers.ImageField(source='receipt_image', required=False, allow_null=True)
    expenseDate = serializers.DateTimeField(source='expense_date')
    isRecurring = serializers.BooleanField(source='is_recurring', required=False)
    recurringType = serializers.CharField(source='recurring_type', required=False, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'title', 'amount', 'category', 'paymentMethod',
            'notes', 'receiptImage', 'expenseDate',
            'isRecurring', 'recurringType', 'tags',
            'createdAt', 'updatedAt',
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['amount'] = float(ret.get('amount', 0) or 0)
        # Add _id alias for frontend compatibility
        ret['_id'] = str(ret['id'])
        return ret


# ───── Income Serializer ─────
class IncomeSerializer(serializers.ModelSerializer):
    paymentSource = serializers.CharField(source='payment_source', required=False)
    incomeDate = serializers.DateTimeField(source='income_date')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Income
        fields = [
            'id', 'source', 'amount', 'description', 'paymentSource',
            'incomeDate', 'notes', 'createdAt', 'updatedAt',
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['amount'] = float(ret.get('amount', 0) or 0)
        ret['_id'] = str(ret['id'])
        return ret


# ───── Budget Serializer ─────
class BudgetSerializer(serializers.ModelSerializer):
    totalMonthlyBudget = serializers.DecimalField(
        source='total_monthly_budget', max_digits=12, decimal_places=2
    )
    warningThreshold = serializers.IntegerField(source='warning_threshold', required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'month', 'year', 'totalMonthlyBudget', 'warningThreshold', 'createdAt', 'updatedAt']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['totalMonthlyBudget'] = float(ret.get('totalMonthlyBudget', 0) or 0)
        ret['_id'] = str(ret['id'])
        return ret


# ───── Report Serializer ─────
class ReportSerializer(serializers.ModelSerializer):
    reportRange = serializers.SerializerMethodField()
    generatedFile = serializers.CharField(source='generated_file', read_only=True, allow_null=True)
    summary = serializers.SerializerMethodField()
    topCategory = serializers.CharField(source='top_category', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'type', 'reportRange', 'format', 'generatedFile',
            'summary', 'topCategory', 'createdAt', 'updatedAt',
        ]

    def get_reportRange(self, obj):
        return {
            'startDate': obj.start_date.isoformat() if obj.start_date else None,
            'endDate': obj.end_date.isoformat() if obj.end_date else None,
        }

    def get_summary(self, obj):
        return {
            'totalExpense': float(obj.total_expense),
            'totalIncome': float(obj.total_income),
            'netSavings': float(obj.net_savings),
            'topCategory': obj.top_category,
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['_id'] = str(ret['id'])
        return ret
