from django.db import models
from django.conf import settings
from django.utils import timezone
from applications.models import Student
from hostels.models import Hostel


class MessMenu(models.Model):
    MEAL_BREAKFAST = 'BREAKFAST'
    MEAL_LUNCH = 'LUNCH'
    MEAL_SNACKS = 'SNACKS'
    MEAL_DINNER = 'DINNER'

    MEAL_CHOICES = [
        (MEAL_BREAKFAST, 'Breakfast (7:30 AM - 9:00 AM)'),
        (MEAL_LUNCH, 'Lunch (12:30 PM - 2:00 PM)'),
        (MEAL_SNACKS, 'Evening Snacks (5:00 PM - 6:00 PM)'),
        (MEAL_DINNER, 'Dinner (7:30 PM - 9:30 PM)'),
    ]

    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='mess_menus')
    date = models.DateField()
    meal = models.CharField(max_length=20, choices=MEAL_CHOICES)
    items = models.TextField(help_text="Menu items, separated by commas (e.g. Idli, Sambar, Chutney, Tea)")
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'meal']
        unique_together = ('hostel', 'date', 'meal')

    def __str__(self):
        return f"{self.hostel.name} - {self.get_meal_display()} on {self.date}"


class MessAttendance(models.Model):
    """
    Tracks meals attended or skipped by students for billing & food-wastage tracking.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mess_attendances')
    date = models.DateField()
    meal = models.CharField(max_length=20, choices=MessMenu.MEAL_CHOICES)
    is_skipped = models.BooleanField(default=False, help_text="Marked by student before cutoff time to claim rebate")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'meal']
        unique_together = ('student', 'date', 'meal')

    def __str__(self):
        status = "SKIPPED" if self.is_skipped else "ATTENDED"
        return f"{self.student.name} - {self.meal} on {self.date} ({status})"


class MessFeedback(models.Model):
    """Student feedback and 1-5 rating on daily meals."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mess_feedbacks')
    date = models.DateField(default=timezone.now)
    meal = models.CharField(max_length=20, choices=MessMenu.MEAL_CHOICES)
    rating = models.PositiveSmallIntegerField(help_text="1 to 5 star rating")
    comments = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rating {self.rating}★ for {self.meal} on {self.date} by {self.student.name}"


class MessFee(models.Model):
    """Monthly mess invoice per student factoring in approved rebates."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mess_fees')
    month = models.PositiveSmallIntegerField(help_text="1 to 12")
    year = models.PositiveIntegerField(default=2026)
    days_present = models.PositiveIntegerField(default=30)
    skipped_meals_count = models.PositiveIntegerField(default=0)
    base_amount = models.DecimalField(max_digits=8, decimal_places=2, default=4500.00)
    rebate_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=4500.00)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('student', 'month', 'year')

    def calculate_total(self):
        self.total_amount = max(0, self.base_amount - self.rebate_amount)
        return self.total_amount

    def __str__(self):
        status = "PAID" if self.is_paid else "DUE"
        return f"Mess Bill ({self.month}/{self.year}) - {self.student.name}: ₹{self.total_amount} ({status})"
