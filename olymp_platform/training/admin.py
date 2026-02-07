from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Submission


class SubmissionResource(resources.ModelResource):
    class Meta:
        model = Submission
        fields = ("id", "user", "problem", "is_correct", "time_spent", "created_at")
        export_order = fields


@admin.register(Submission)
class SubmissionAdmin(ImportExportModelAdmin):
    resource_class = SubmissionResource
    list_display = ("id", "user", "problem", "is_correct", "time_spent", "created_at")
    list_filter = ("is_correct", "created_at", "problem__subject", "problem__topic")
    search_fields = ("user__username", "problem__title", "problem__topic")
    ordering = ("-created_at",)
    autocomplete_fields = ("user", "problem")
