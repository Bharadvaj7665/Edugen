# projects/views.py
import boto3
from django.conf import settings
from django.db.models import F
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action # We'll use this for custom actions
from .models import Project
from users.models import UserProfile
from .serializers import *
from urllib.parse import urlparse
from .tasks import generate_content_task,generate_audio_task
from .utils import download_file_from_s3 , extract_text_from_file,generate_podcast_script_from_text,calculate_cost

class ProjectViewSet(viewsets.GenericViewSet):
    """
    A single ViewSet to handle all Project-related actions:
    - Listing projects
    - Creating project records
    - Retrieving a single project
    - Uploading files
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Action to list all of the user's projects."""
        queryset = Project.objects.filter(user=request.user).order_by('-created_at')
        serializer = ProjectDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Action to create a new project record. Does NOT start any tasks."""
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # The only job of this method is to create the project record.
        project = serializer.save(user=request.user)

        response_serializer = ProjectDetailSerializer(project)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """
        Action to delete a project, its generated content, and its S3 file.
        """
        project = self.get_object() # Uses the existing helper to find the project

        # --- S3 File Deletion Logic ---
        if project.s3_file_key:
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=project.s3_file_key
                )
                print(f"Successfully deleted {project.s3_file_key} from S3.")
            except Exception as e:
                # Log the error but don't block the database deletion
                print(f"Error deleting {project.s3_file_key} from S3: {e}")
        # --- End of S3 Logic ---

        # Deleting the project object will automatically delete all related
        # GeneratedContent objects because of the `on_delete=models.CASCADE` setting.
        project.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


    serializer_map = {
        GeneratedContent.ContentType.PRESENTATION: PresentationGenerateSerializer,
        GeneratedContent.ContentType.FLASHCARDS: FlashcardGenerateSerializer,
        GeneratedContent.ContentType.MCQ_SET: MCQGenerateSerializer,
        GeneratedContent.ContentType.PODCAST: PodcastGenerateSerializer,
    }
    @action(detail=True, methods=['post'])
    def generate_content(self, request, pk=None):
        project = self.get_object()
        content_type = request.data.get('content_type')

        user = project.user
        user_profile ,created = UserProfile.objects.get_or_create(user=user)
        if created:
            print(f"Profile for user {user.id} was created by generate_content api.")
        
        if user_profile.token_balance < 0.09:
            return Response({"error": "Insufficient tokens"}, status=status.HTTP_400_BAD_REQUEST)

        serializer_class = self.serializer_map.get(content_type)
        if not serializer_class:
            return Response({"error": f"Invalid content type: {content_type}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        generations_options = serializer.validated_data
        print(generations_options,"generated_options")
        # 1. Create the GeneratedContent record first, with a PENDING status.
        content_record, created = GeneratedContent.objects.update_or_create(
            project=project,
            content_type=content_type,
            defaults={
                'task_status': GeneratedContent.TaskStatus.PENDING,
                's3_url': None
            }
        )

        # 2. Start the Celery task, passing the new record's ID.
        task = generate_content_task.delay(content_record.id, generations_options)

        # 3. Save the task ID to the record.
        content_record.task_id = task.id
        content_record.save()

        return Response(
            {"message": f"Content generation for '{content_type}' started.", "task_id": task.id,"content_id":content_record.id},
            status=status.HTTP_202_ACCEPTED
        )


    #Script generation
    @action(detail=True,methods=['post'],serializer_class=PodcastScriptGenerateSerializer)
    def generate_podcast_script(self,request,pk=None):
        project = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = project.user
        user_profile ,created = UserProfile.objects.get_or_create(user=user)
        if created:
            print(f"Profile for user {user.id} was created by generate_content api.")
        
        if user_profile.token_balance < 0.09:
            return Response({"error": "Insufficient tokens"}, status=status.HTTP_400_BAD_REQUEST)

        #This is a fast operation, so we can do it synchoronously
        local_path = download_file_from_s3(project.s3_file_key)
        text_content = extract_text_from_file(local_path)

        script_data, usage = generate_podcast_script_from_text(text_content,serializer.validated_data,project.original_file_name)

        cost = calculate_cost("gpt-5-nano",usage)
        request.user.profile.token_balance = F('token_balance') - cost
        request.user.profile.save()
        
        #Return script directly to frontend
        return Response(script_data,status = status.HTTP_200_OK)


    #Audio generation
    @action(detail=True,methods=['post'],serializer_class=PodcastAudioGenerateSerializer)
    def generate_podcast_audio(self,request,pk=None):
        project = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        #This is a slow part , so we use celery
        content_record, created = GeneratedContent.objects.update_or_create(
            project=project,
            content_type=GeneratedContent.ContentType.PODCAST,
            defaults={
                'task_status': GeneratedContent.TaskStatus.PENDING,
                's3_url': None
            }
        )

        # 2. Start the Celery task, passing the new record's ID.
        task = generate_audio_task.delay(content_record.id, serializer.validated_data)

        # 3. Save the task ID to the record.
        content_record.task_id = task.id
        content_record.save()

        return Response(
            {"message": "Podcast audio generation started.", "task_id": task.id,"content_id":content_record.id},
            status=status.HTTP_202_ACCEPTED
        )

    # Helper method to get a single project object
    def get_object(self):
        pk = self.kwargs.get('pk')
        queryset = Project.objects.filter(user=self.request.user)
        obj = generics.get_object_or_404(queryset, pk=pk)
        return obj

    def retrieve(self, request, pk=None):
        """Action to retrieve a single project."""
        queryset = Project.objects.filter(user=request.user)
        project = generics.get_object_or_404(queryset, pk=pk)
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], serializer_class=FileUploadSerializer)
    def upload_file(self, request):
        """Custom action to handle only the file upload to S3."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data['file']

        s3_key = f"uploads/{request.user.id}/{file_obj.name}"
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

        try:
            s3_client.upload_fileobj(file_obj, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        except Exception as e:
            return Response({"error": f"Failed to upload to S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        return Response({
            "s3_file_key": s3_url,
            "original_file_name": file_obj.name
        }, status=status.HTTP_200_OK)

   
    
    
    

    @action(detail=False, methods=['post'], serializer_class=FileUpdateSerializer)
    def update_file(self, request):
        """Custom action to update an existing file in S3."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file_obj = serializer.validated_data['file']
        s3_url = serializer.validated_data['s3_url']

        # Extract key from S3 URL
        parsed_url = urlparse(s3_url)
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        expected_host = f"{bucket}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"

        if expected_host not in parsed_url.netloc:
            return Response({"error": "Invalid S3 URL for this bucket."}, status=status.HTTP_400_BAD_REQUEST)

        s3_key = parsed_url.path.lstrip('/')  # Remove leading slash

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        try:
            s3_client.upload_fileobj(file_obj, bucket, s3_key)
        except Exception as e:
            return Response({"error": f"Failed to update file in S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "File successfully updated in S3.",
            "s3_file_key": s3_url,
            "original_file_name": file_obj.name
        }, status=status.HTTP_200_OK)


# --- NEW VIEWSET FOR POLLING ---
class GeneratedContentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A ViewSet for retrieving and checking the status of GeneratedContent.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GeneratedContentSerializer # We'll use the existing serializer

    def get_queryset(self):
        """Ensures users can only access their own content."""
        return GeneratedContent.objects.filter(project__user=self.request.user)