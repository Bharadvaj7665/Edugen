# projects/models.py
from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    s3_file_key = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a human-readable string representation of the Project instance,
        which is the same as the project title.
        """
        
        return self.title

class GeneratedContent(models.Model):
    class ContentType(models.TextChoices):
        PRESENTATION = 'PPT', 'Presentation'
        FLASHCARDS = 'FLASH', 'Flashcards'
        MCQ_SET = 'MCQ', 'MCQ Set'
        PODCAST = 'POD', 'Podcast'
    
    class TaskStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILURE = 'FAILURE', 'Failure'

    project = models.ForeignKey(Project, related_name='generated_content', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=5, choices=ContentType.choices)
    # content_data = models.JSONField(blank=True,null=True)
    s3_url = models.URLField(max_length=1024, blank=True, null=True) # Will be filled upon task success
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW FIELDS ADDED HERE
    task_id = models.CharField(max_length=50, blank=True, null=True)
    task_status = models.CharField(max_length=10, choices=TaskStatus.choices, default=TaskStatus.PENDING)

    class Meta:
        unique_together = ('project', 'content_type')
        
    def __str__(self):
        return f"{self.get_content_type_display()} for {self.project.title}"

    