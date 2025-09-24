# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer
from .models import UserProfile

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves the profile and token balance for the authenticated user.
        """
        # user_profile = request.user.profile
        user_profile ,created = UserProfile.objects.get_or_create(user=request.user)
        if created:
            print(f"Profile for user {request.user.id} was created by user_profile api.")
        # user_profile = user_profile.profile
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)