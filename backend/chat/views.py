# chat/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChatSession
from .serializers import ChatSessionSerializer, PostMessageSerializer
from .tasks import get_ai_chat_response_task

class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['post'], serializer_class=PostMessageSerializer)
    def post_message(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_id = serializer.validated_data['project_id']
        message_text = serializer.validated_data['message']

        # Find or create the chat session for the project
        session, created = ChatSession.objects.get_or_create(
            project_id=project_id,
            user=request.user
        )

        # Save the user's message
        session.messages.create(sender='USER', message=message_text)

        # Start the background task to get the AI's response
        get_ai_chat_response_task.delay(session.id, message_text)

        return Response(
            {"message": "Message received, AI is responding.","session_id": session.id},
            status=status.HTTP_202_ACCEPTED
        )