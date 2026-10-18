from django.contrib import admin

from .models import Course, CourseOffering, CoursePrerequisite, FacultyProfile, FeeStructure, GradeBand, GradingScheme, Program, Scholarship, Semester

for model in [Program, Semester, Course, CoursePrerequisite, FacultyProfile, CourseOffering, GradingScheme, GradeBand, FeeStructure, Scholarship]:
    admin.site.register(model)
