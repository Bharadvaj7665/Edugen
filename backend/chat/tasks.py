# chat/tasks.py
from celery import shared_task
import openai
from .models import ChatSession, ChatMessage
from projects.utils import download_file_from_s3, extract_text_from_file

@shared_task
def get_ai_chat_response_task(chat_session_id, user_message):
    session = ChatSession.objects.get(id=chat_session_id)
    project = session.project

    # 1. Get the document context
    local_file_path = download_file_from_s3(project.s3_file_key)
    document_context = extract_text_from_file(local_file_path)

    # 2. Construct the prompt
    prompt = f"""
    You are a helpful assistant. A user is asking a question about a document.
    Here is the context from the document:
    ---
    {document_context[:6000]}
    ---
    Here is the user's question: "{user_message}"

    Please provide a clear and helpful answer based on the document context.
    """

    # 3. Call OpenAI API
    response = openai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )
    ai_message_text = response.choices[0].message.content

    # 4. Save the AI's response
    ChatMessage.objects.create(
        session=session,
        sender=ChatMessage.SenderType.AI,
        message=ai_message_text
    )
    return "AI response generated successfully."