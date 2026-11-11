from django.contrib import admin
# Register student-related models in the Django admin panel
# to enable administrative management of student profiles,
# profile change requests, uploaded documents, and ID sequences.
from .models import ProfileChangeRequest, Student, StudentDocument, StudentIdSequence

admin.site.register(Student)
admin.site.register(ProfileChangeRequest)
admin.site.register(StudentDocument)
admin.site.register(StudentIdSequence)
