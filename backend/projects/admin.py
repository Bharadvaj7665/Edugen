from django.contrib import admin
from .models import Project, GeneratedContent

class GeneratedContentInline(admin.TabularInline):
    model = GeneratedContent
    extra = 0  # Don't show extra empty forms for adding new content

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'original_file_name', 'created_at')
    inlines = [GeneratedContentInline]

# We can also register GeneratedContent on its own if we want
@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ('project', 'content_type', 'created_at')