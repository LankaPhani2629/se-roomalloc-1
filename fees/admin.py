from django.contrib import admin
from .models import FeeStructure, FeePayment


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('room_type', 'academic_year', 'amount', 'due_days')
    list_filter = ('academic_year', 'room_type')


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'allocation', 'amount', 'payment_mode', 'transaction_id', 'payment_date', 'status')
    list_filter = ('status', 'payment_mode')
    search_fields = ('receipt_no', 'transaction_id', 'allocation__student__name', 'allocation__student__student_id')
