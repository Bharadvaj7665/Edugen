# chat/models.py
from django.db import models
from django.contrib.auth.models import User
from projects.models import Project

class ChatSession(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="chat_session")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for project: {self.project.title}"

class ChatMessage(models.Model):
    class SenderType(models.TextChoices):
        USER = 'USER', 'User'
        AI = 'AI', 'AI'

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=4, choices=SenderType.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}..."