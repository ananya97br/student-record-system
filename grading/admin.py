from django.contrib import admin

from .models import AssessmentComponent, CourseResult, GradeRecord, TranscriptVerification

admin.site.register(AssessmentComponent)
admin.site.register(GradeRecord)
admin.site.register(CourseResult)
admin.site.register(TranscriptVerification)
