from django.db import models
from django.conf import settings
from django.db.models import F, Q, CheckConstraint


class Hostel(models.Model):
    TYPE_BOYS = 'BOYS'
    TYPE_GIRLS = 'GIRLS'
    TYPE_CHOICES = [
        (TYPE_BOYS, 'Boys Hostel'),
        (TYPE_GIRLS, 'Girls Hostel'),
    ]

    name = models.CharField(max_length=100, unique=True)
    hostel_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    total_rooms = models.PositiveIntegerField(default=0)
    warden = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_hostels',
        limit_choices_to={'role': 'WARDEN'}
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def update_room_count(self):
        self.total_rooms = self.rooms.count()
        self.save(update_fields=['total_rooms'])

    @property
    def total_capacity(self):
        return sum(room.capacity for room in self.rooms.all())

    @property
    def total_occupied(self):
        return sum(room.occupied_count for room in self.rooms.all())

    @property
    def total_vacant(self):
        return self.total_capacity - self.total_occupied

    def __str__(self):
        return f"{self.name} ({self.get_hostel_type_display()})"


class Room(models.Model):
    TYPE_SINGLE = 'SINGLE'
    TYPE_DOUBLE = 'DOUBLE'
    TYPE_TRIPLE = 'TRIPLE'
    TYPE_FOUR = 'FOUR_SHARING'
    ROOM_TYPE_CHOICES = [
        (TYPE_SINGLE, 'Single Room (1 Bed)'),
        (TYPE_DOUBLE, 'Double Sharing (2 Beds)'),
        (TYPE_TRIPLE, 'Triple Sharing (3 Beds)'),
        (TYPE_FOUR, 'Four Sharing (4 Beds)'),
    ]

    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_FULL = 'FULL'
    STATUS_MAINTENANCE = 'MAINTENANCE'
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_FULL, 'Full'),
        (STATUS_MAINTENANCE, 'Under Maintenance'),
    ]

    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    floor_no = models.IntegerField(default=0, help_text="0 for Ground floor, 1 for 1st floor, etc.")
    room_no = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=2)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default=TYPE_DOUBLE)
    occupied_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    class Meta:
        ordering = ['hostel', 'floor_no', 'room_no']
        unique_together = ('hostel', 'room_no')
        constraints = [
            CheckConstraint(
                condition=Q(occupied_count__lte=F('capacity')),
                name='room_capacity_check'
            )
        ]

    @property
    def vacancy(self):
        return max(0, self.capacity - self.occupied_count)

    @property
    def is_available(self):
        return self.status == self.STATUS_AVAILABLE and self.vacancy > 0

    def refresh_status(self):
        """Update room status based on occupied_count and maintenance."""
        if self.status != self.STATUS_MAINTENANCE:
            if self.occupied_count >= self.capacity:
                self.status = self.STATUS_FULL
            else:
                self.status = self.STATUS_AVAILABLE

    def save(self, *args, **kwargs):
        self.refresh_status()
        super().save(*args, **kwargs)
        if self.hostel_id:
            self.hostel.update_room_count()

    def __str__(self):
        return f"{self.hostel.name} - Rm {self.room_no} (Fl {self.floor_no})"
