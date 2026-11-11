from django.contrib import admin

from .models import AssessmentComponent, CourseResult, GradeRecord, TranscriptVerification

admin.site.register(AssessmentComponent)
admin.site.register(GradeRecord)


@admin.register(CourseResult)
class CourseResultAdmin(admin.ModelAdmin):
    readonly_fields = tuple(field.name for field in CourseResult._meta.fields)
    list_display = ("student", "offering", "final_score", "letter_grade", "is_locked")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(TranscriptVerification)
