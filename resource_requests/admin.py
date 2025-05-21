from django.contrib import admin
from .models import Department, Resource, ResourceRequest, Ledger, UserProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name",)


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "request_id",
        "department",
        "requestor",
        "resource",
        "required_date",
        "status",
    )
    list_filter = ("status", "department", "required_date")
    search_fields = ("request_id", "requestor__username", "purpose")
    readonly_fields = ("request_id", "submitted_at")
    date_hierarchy = "required_date"


@admin.register(Ledger)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("ledger_id", "request", "status", "created_at")
    list_filter = ("status", "request__department", "request__required_date")
    search_fields = ("ledger_id", "request__request_id")
    readonly_fields = ("ledger_id", "created_at")
    date_hierarchy = "created_at"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "department")
    list_filter = ("user_type", "department")
    search_fields = ("user__username", "user__email")
