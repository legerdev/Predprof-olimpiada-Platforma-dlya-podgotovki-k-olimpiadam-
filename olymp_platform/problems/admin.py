from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Problem, ProblemTemplate


class ProblemTemplateResource(resources.ModelResource):
    class Meta:
        model = ProblemTemplate
        fields = (
            "id","key","display_title","subject","topic","difficulty",
            "statement_template","generator_key","params_schema" ,"is_active"
        )
        export_order = fields



@admin.register(ProblemTemplate)
class ProblemTemplateAdmin(ImportExportModelAdmin):
    resource_class = ProblemTemplateResource
    list_display = ("id", "key", "subject", "topic", "difficulty", "generator_key", "hint", "is_active")
    list_filter = ("subject", "topic", "difficulty", "is_active")
    search_fields = ("key", "topic", "statement_template", "generator_key")


@admin.register(Problem)
class ProblemAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "subject", "topic", "difficulty", "is_generated", "hint","is_active")
    list_filter = ("subject", "topic", "difficulty", "is_generated", "is_active")
    search_fields = ("title", "text", "correct_answer", "topic")
    ordering = ("-id",)
