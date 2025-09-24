# projects/views.py (temporary addition)
import boto3
from django.conf import settings

# Call this function to test your S3 connection
def test_s3_connection():
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        print("S3 connection and permissions successful!")
    except Exception as e:
        print(f"S3 connection failed: {e}")
        
# Call it once at the top of your ProjectViewSet
test_s3_connection()

# Now proceed with your ProjectViewSet class
# ...