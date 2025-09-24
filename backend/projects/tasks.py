# projects/tasks.py
import os
import boto3
from celery import shared_task
from django.conf import settings
from .models import GeneratedContent
from .utils import (download_file_from_s3, extract_text_from_file, generate_ppt_from_text,
                     generate_flashcards_from_text, generate_mcqs_from_text,generate_podcast_audio_from_script)
from django.db.models import F
from .utils import calculate_cost
from users.models import UserProfile
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_content_task(generated_content_id,generations_options):
    logger.info("generations_options: ",generations_options)
    content_record = GeneratedContent.objects.get(id=generated_content_id)
    if content_record.s3_url:
        try:
            old_s3_key = content_record.s3_url.split('.com/', 1)[1]
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=old_s3_key
            )
            print(f"Successfully deleted old S3 object: {old_s3_key}")
        except Exception as e:
            # Log the error but don't stop the task.
            # It's better to have an orphaned file than to fail the entire generation.
            print(f"Could not delete old S3 object. Error: {e}")
    project = content_record.project
    user = project.user
    user_profile,created = UserProfile.objects.get_or_create(user=user)
    if created:
        print(f"Profile for user {user.id} was created by a celery worker.")
    
    try:
        # 1. Download the original file from S3
        print(f"Attempting to download s3 file : {project.s3_file_key}")
        local_file_path = download_file_from_s3(project.s3_file_key)

        # 2. Extract text from the file
        text_content = extract_text_from_file(local_file_path)
        if not text_content.strip():
            raise ValueError("Extracted text is empty. Cannot generate content.")

        # 3. Call the appropriate AI generation function
        final_file_path = None
        total_cost = 0
        usage = None
        model_used = "gpt-5-nano"
        if content_record.content_type == GeneratedContent.ContentType.PRESENTATION:
            final_file_path,total_cost = generate_ppt_from_text(text_content,generations_options)
        
        elif content_record.content_type == GeneratedContent.ContentType.FLASHCARDS:
             final_file_path,total_cost = generate_flashcards_from_text(text_content,generations_options)

        elif content_record.content_type == GeneratedContent.ContentType.MCQ_SET:
             final_file_path,total_cost = generate_mcqs_from_text(text_content,generations_options)

        # elif content_record.content_type == GeneratedContent.ContentType.PODCAST:
        #      audio_file_path, _,usage = generate_podcast_from_text(text_content,generations_options)
        #      final_file_path = audio_file_path
        #      usage = usage
        
        if total_cost>0 :
            user_profile.token_balance = F('token_balance') - total_cost
            user_profile.save()
            

        if not final_file_path:
            raise ValueError("Content generation failed.")

        # 4. Upload the newly generated file back to S3
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        generated_s3_key = f"generated/{project.id}/{content_record.id}_{os.path.basename(final_file_path)}"
        s3_client.upload_file(final_file_path, settings.AWS_STORAGE_BUCKET_NAME, generated_s3_key)
        
        # 5. Update the record with SUCCESS status and the final S3 URL
        s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{generated_s3_key}"
        content_record.s3_url = s3_url
        content_record.task_status = GeneratedContent.TaskStatus.SUCCESS
        content_record.save()
        
        # Clean up the local generated file
        if os.path.exists(final_file_path):
            os.remove(final_file_path)

        return "Task Completed Successfully"

    except Exception as e:
        content_record.task_status = GeneratedContent.TaskStatus.FAILURE
        content_record.save()
        # Re-raise the exception so Celery can log it properly
        raise e

@shared_task
def generate_audio_task(generated_content_id, generation_options):
    """A dedicated task that only handles audio generation and upload."""
    content_record = GeneratedContent.objects.get(id=generated_content_id)
    script_text = generation_options.get('script_text')
    if content_record.s3_url:
        try:
            old_s3_key = content_record.s3_url.split('.com/', 1)[1]
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=old_s3_key
            )
            print(f"Successfully deleted old S3 object: {old_s3_key}")
        except Exception as e:
            # Log the error but don't stop the task.
            # It's better to have an orphaned file than to fail the entire generation.
            print(f"Could not delete old S3 object. Error: {e}")

    try:
        if not script_text:
            raise ValueError("Script text cannot be empty.")

        audio_file_path = generate_podcast_audio_from_script(script_text, generation_options)

        # Upload the generated MP3 to S3
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        generated_s3_key = f"generated/{content_record.project.id}/{content_record.id}_podcast.mp3"
        s3_client.upload_file(audio_file_path, settings.AWS_STORAGE_BUCKET_NAME, generated_s3_key)

        # Update the record with the final URL
        content_record.s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{generated_s3_key}"
        content_record.task_status = GeneratedContent.TaskStatus.SUCCESS
        content_record.save()

        os.remove(audio_file_path) # Clean up temp file
        return "Audio task completed."

    except Exception as e:
        content_record.task_status = GeneratedContent.TaskStatus.FAILURE
        content_record.save()
        raise e

    