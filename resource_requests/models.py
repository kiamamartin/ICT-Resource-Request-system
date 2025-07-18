#models.py

from django.db import models
from django.contrib.auth.models import User
import uuid


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    USER_TYPES = [
        ('admin', 'Admin'),
        ('director', 'Director'),
        ('staff', 'Staff'),
        
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='staff')
    is_director = models.BooleanField(default=False)
    is_deputy_director = models.BooleanField(default=False)
    has_approval_rights = models.BooleanField(default=False)
    approval_rights_delegated_at = models.DateTimeField(null=True, blank=True)
    approval_rights_delegation_end = models.DateTimeField(null=True, blank=True)
    approval_rights_delegated_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='delegated_to'
    )
    is_admin = models.BooleanField(default=False)
    theme_preference = models.CharField(
        max_length=10,
        default="light",
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
        ],
    )
    signature_image = models.ImageField(upload_to="signatures/", blank=True, null=True)

    def save(self, *args, **kwargs):
        # If this user is being set as director, ensure they have approval rights
        if self.is_director and not self.has_approval_rights:
            self.has_approval_rights = True
        
        # If this is a new user and they're being set as deputy director,
        # ensure they don't have approval rights by default
        if self.pk is None and self.is_deputy_director:
            self.has_approval_rights = False
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.user.username


class ResourceRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    DURATION_CHOICES = [
        ("1_hour", "1 Hour"),
        ("2_hours", "2 Hours"),
        ("half_day", "Half Day"),
        ("full_day", "Full Day"),
        ("multiple_days", "Multiple Days"),
    ]

    request_id = models.CharField(max_length=20, unique=True)
    requestor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requests"
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    purpose = models.TextField()
    required_date = models.DateField()
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    additional_info = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requests",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    physical_copy_stamped = models.BooleanField(default=False)
    director_notes = models.TextField(blank=True, null=True)
    signature_image = models.ImageField(upload_to="signatures/", blank=True, null=True)
    stamp_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request {self.request_id} - {self.resource}"


class Ledger(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    ledger_id = models.CharField(max_length=20, unique=True)
    request = models.OneToOneField(
        ResourceRequest, on_delete=models.CASCADE, related_name="ledger"
    )
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    requestor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ledger_entries"
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="approved_ledger_entries"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ledger {self.ledger_id} - {self.resource}"

class DelegationLog(models.Model):
    delegated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegations_made')
    delegated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delegations_received')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_end_date = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Delegation from {self.delegated_by} to {self.delegated_to}"