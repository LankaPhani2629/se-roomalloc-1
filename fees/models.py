import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from allocations.models import Allocation


class FeeStructure(models.Model):
    ROOM_TYPE_CHOICES = [
        ('SINGLE', 'Single Room (1 Bed)'),
        ('DOUBLE', 'Double Sharing (2 Beds)'),
        ('TRIPLE', 'Triple Sharing (3 Beds)'),
        ('FOUR_SHARING', 'Four Sharing (4 Beds)'),
    ]

    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    academic_year = models.CharField(max_length=20, default='2026-2027')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_days = models.PositiveIntegerField(default=7, help_text="Number of days granted after allocation to pay the fee")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('room_type', 'academic_year')
        ordering = ['academic_year', 'room_type']

    def __str__(self):
        return f"{self.get_room_type_display()} ({self.academic_year}): ₹{self.amount}"


class FeePayment(models.Model):
    MODE_CASH = 'CASH'
    MODE_ONLINE = 'ONLINE'
    MODE_UPI = 'UPI'
    MODE_BANK = 'BANK_TRANSFER'
    MODE_CHEQUE = 'CHEQUE'
    MODE_CHOICES = [
        (MODE_CASH, 'Cash'),
        (MODE_ONLINE, 'Online Net Banking'),
        (MODE_UPI, 'UPI / QR Code'),
        (MODE_BANK, 'Bank Transfer / NEFT'),
        (MODE_CHEQUE, 'Cheque / Demand Draft'),
    ]

    STATUS_SUCCESS = 'SUCCESS'
    STATUS_PENDING = 'PENDING'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Successful'),
        (STATUS_PENDING, 'Pending Verification'),
        (STATUS_FAILED, 'Failed'),
    ]

    allocation = models.ForeignKey(Allocation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_UPI)
    transaction_id = models.CharField(max_length=100, unique=True)
    receipt_no = models.CharField(max_length=50, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_payments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    remarks = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-payment_date']

    @classmethod
    def generate_receipt_no(cls):
        prefix = timezone.now().strftime("RCP%Y%m")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{unique_suffix}"

    def __str__(self):
        return f"Receipt #{self.receipt_no} - ₹{self.amount} for {self.allocation.student.name}"
