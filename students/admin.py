from django.contrib import admin

from .models import ProfileChangeRequest, Student, StudentDocument, StudentIdSequence

admin.site.register(Student)
admin.site.register(ProfileChangeRequest)
admin.site.register(StudentDocument)
admin.site.register(StudentIdSequence)
