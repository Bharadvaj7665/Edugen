# chat/serializers.py
from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'project', 'user', 'created_at', 'messages']

class PostMessageSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    message = serializers.CharField()