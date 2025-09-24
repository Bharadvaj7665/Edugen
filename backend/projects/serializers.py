from rest_framework import serializers
from .models import *
from chat.serializers import ChatSessionSerializer

class GeneratedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedContent
        fields = ['id', 'content_type', 's3_url', 'created_at', 'task_id', 'task_status']
        read_only_fields = ['project', 'task_id']

class ProjectCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ['id', 'title', 'original_file_name', 's3_file_key']
        read_only_fields = ['user', 'task_id']

from celery.result import AsyncResult

class ProjectDetailSerializer(serializers.ModelSerializer):
    generated_content = GeneratedContentSerializer(many=True, read_only=True)
    chat_session = ChatSessionSerializer( read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'original_file_name', 's3_file_key', 'generated_content', 'chat_session', 'created_at']

    def get_task_status(self, obj):
        if not obj.task_id:
            return "Not Started"
        result = AsyncResult(obj.task_id)
        return result.status
    


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class FileUpdateSerializer(serializers.Serializer):
    file = serializers.FileField()
    s3_url = serializers.URLField()


class GenerateContentSerializer(serializers.Serializer):
    # Get the choices directly from the model for validation
    CONTENT_CHOICES = GeneratedContent.ContentType.choices
    content_type = serializers.ChoiceField(choices=CONTENT_CHOICES)

class PresentationGenerateSerializer(GenerateContentSerializer):
    # Get the choices directly from the model for validation
    content_type = serializers.ChoiceField(choices=[GeneratedContent.ContentType.PRESENTATION])
    slides_count = serializers.IntegerField(min_value=3, max_value=20, default=10)
    include_images = serializers.BooleanField(default=False)

class FlashcardGenerateSerializer(GenerateContentSerializer):
    # Get the choices directly from the model for validation
    content_type = serializers.ChoiceField(choices=[GeneratedContent.ContentType.FLASHCARDS])
    cards_count = serializers.IntegerField(min_value=5, max_value=50, default=20)
    card_type = serializers.ChoiceField(choices=["qa","true_false","fill_blank"], default="qa")
    difficulty = serializers.ChoiceField(choices=["easy","medium","hard","mixed"], default="mixed")

class MCQGenerateSerializer(GenerateContentSerializer):
    # Get the choices directly from the model for validation
    content_type = serializers.ChoiceField(choices=[GeneratedContent.ContentType.MCQ_SET])
    questions_count = serializers.IntegerField(min_value=5, max_value=30, default=15)
    questions_type = serializers.ChoiceField(choices=["single_correct","multiple_correct","true_false"], default="single_correct")
    difficulty = serializers.ChoiceField(choices=["easy","medium","hard","mixed"], default="mixed")

class PodcastGenerateSerializer(GenerateContentSerializer):
    content_type = serializers.ChoiceField(choices=[GeneratedContent.ContentType.PODCAST])
    podcast_length = serializers.ChoiceField(choices=["quick", "medium", "comprehensive"], default="medium")
    content_focus = serializers.ChoiceField(choices=["full_document", "key_concepts", "summary"], default="full_document")
    voice_style = serializers.ChoiceField(choices=["neutral", "enthusiastic", "formal", "conversational"], default="neutral")
    voice_gender = serializers.ChoiceField(choices=["male", "female"], default="female")
    voice_accent = serializers.ChoiceField(choices=["american", "british", "indian", "australian", "canadian"], default="american")


class PodcastScriptGenerateSerializer(GenerateContentSerializer):
    podcast_length = serializers.ChoiceField(choices=["quick", "medium", "comprehensive"], default="medium")
    content_focus = serializers.ChoiceField(choices=["full_document", "key_concepts", "summary"], default="full_document")

class PodcastAudioGenerateSerializer(GenerateContentSerializer):
    script_text = serializers.CharField()
    voice_style = serializers.ChoiceField(choices=["neutral", "enthusiastic", "formal", "conversational"], default="neutral")
    voice_gender = serializers.ChoiceField(choices=["male", "female"], default="female")
    voice_accent = serializers.ChoiceField(choices=["american", "british", "indian", "australian", "canadian"], default="american")

