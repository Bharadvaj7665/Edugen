# EduMind SaaS Platform

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-blue.svg" alt="Django">
  <img src="https://img.shields.io/badge/Django%20Rest%20Framework-3.16-red.svg" alt="DRF">
  <img src="https://img.shields.io/badge/Celery-5.5-green.svg" alt="Celery">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-blue.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Containerization-Docker-blue.svg" alt="Docker">
</p>

This document provides a complete guide for developers working on the EduMind SaaS Platform. Its goal is to be the single source of truth, enabling any developer to set up, run, contribute to, and deploy the project without needing additional assistance.

---

## 1. Project Overview

The EduMind SaaS Platform is a backend service that transforms user-uploaded documents into various educational formats. It is designed to be a robust, scalable, and asynchronous system that can handle long-running content generation tasks, making it ideal for creating rich learning experiences from source materials.

### High-Level Features

-   **Secure User Authentication**: Manages user accounts and profiles.
-   **Project-Based Organization**: Users create "projects" that contain a source document and all content generated from it.
-   **Asynchronous Content Generation**: Utilizes a task queue to generate content without blocking the user interface or API.
-   **Multiple Content Formats**:
    -   Presentations (.pptx)
    -   Flashcards (PDF/JSON)
    -   Multiple-Choice Quizzes (JSON)
    -   Podcasts (Script Generation & Text-to-Speech)
-   **Cloud Storage**: Integrates with Amazon S3 for scalable and durable file storage.
-   **Usage Tracking**: Includes a basic token system to monitor and debit costs associated with AI service usage.

---

## 2. Tech Stack

| Category                 | Technology / Service                               |
| ------------------------ | -------------------------------------------------- |
| **Backend Framework**    | Django 5.2                                         |
| **API Framework**        | Django Rest Framework (DRF) 3.16                   |
| **Database**             | PostgreSQL 15                                      |
| **Asynchronous Tasks**   | Celery 5.5                                         |
| **Message Broker**       | Redis 7                                            |
| **Containerization**     | Docker & Docker Compose                            |
| **File Storage**         | Amazon S3                                          |
| **Web/ASGI Server**      | Gunicorn / Uvicorn                                 |
| **AI / ML Services**     | OpenAI API                                         |
| **Text-to-Speech**       | edge-tts                                           |
| **Authentication**       | `mozilla-django-oidc` (OIDC), JWT (presumed for API) |
| **Python Environment**   | `venv`                                             |

---

## 3. Folder Structure

The project follows a standard Django "apps" structure, where each major feature is encapsulated in its own directory.

```
edumind_django/
├── .env                    # (To be created) Local environment variables and secrets
├── docker-compose.yml      # Defines and configures all services (web, db, celery, redis)
├── Dockerfile              # Instructions to build the Django application container
├── manage.py               # Django's command-line utility
├── requirements.txt        # Python package dependencies
├── README.md               # This file
│
├── edumind_saas/           # Core Django project folder
│   ├── settings.py         # Main project settings
│   ├── urls.py             # Root URL configuration
│   ├── celery.py           # Celery app configuration
│   └── asgi.py             # ASGI entrypoint for the application server
│
├── users/                  # Django app for User models, profiles, and authentication
│   ├── models.py           # UserProfile model
│   ├── views.py            # API views for user actions
│   ├── urls.py             # App-specific URLs
│   └── serializers.py      # DRF serializers for user models
│
├── projects/               # Django app for core project logic (uploads, generation)
│   ├── models.py           # Project and GeneratedContent models
│   ├── views.py            # API views for projects and content generation
│   ├── tasks.py            # Celery tasks for asynchronous content generation
│   ├── utils.py            # Helper functions (file processing, AI calls, etc.)
│   └── url.py              # App-specific URLs
│
├── chat/                   # Django app for chat functionality
│
└── uploads/                # (Local) Temporary storage for file uploads (not used in S3 config)
```

---

## 4. Setup Instructions

The project is fully containerized with Docker, which is the recommended way to run it locally.

### 4.1. Prerequisites
-   [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/install/)
-   [Git](https://git-scm.com/)

### 4.2. Local Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd edumind_django
    ```

2.  **Create Environment File**
    Create a file named `.env` in the project root. Copy the contents of the example below and replace the placeholder values with your actual credentials.

    ```env
    # .env.example

    # Django Settings
    DJANGO_SECRET_KEY='django-insecure-your-strong-secret-key-here'
    DJANGO_DEBUG='True'

    # Database (must match docker-compose.yml)
    POSTGRES_DB=edumind_db
    POSTGRES_USER=edumind_user
    POSTGRES_PASSWORD=jkateracqweqjhfmgl

    # Redis (must match docker-compose.yml)
    REDIS_HOST=redis
    REDIS_PORT=6379

    # AWS S3 Credentials for file storage
    AWS_ACCESS_KEY_ID='YOUR_AWS_ACCESS_KEY'
    AWS_SECRET_ACCESS_KEY='YOUR_AWS_SECRET_KEY'
    AWS_STORAGE_BUCKET_NAME='your-unique-s3-bucket-name'
    AWS_S3_REGION_NAME='your-s3-bucket-region' # e.g., us-east-1

    # External API Keys
    OPENAI_API_KEY='sk-your-openai-api-key'
    ```

3.  **Build and Run Services**
    This command builds the images and starts the Django app, Celery worker, database, and Redis containers.
    ```bash
    docker-compose up --build
    ```
    To run in detached mode, add the `-d` flag: `docker-compose up -d --build`.

4.  **Apply Database Migrations**
    In a separate terminal, execute the `migrate` command inside the running `app` container.
    ```bash
    docker-compose exec app python manage.py migrate
    ```

5.  **Create a Superuser (Optional)**
    To access the Django Admin interface, create an admin user.
    ```bash
    docker-compose exec app python manage.py createsuperuser
    ```

### 4.3. Accessing the Application
-   **API Root**: `http://localhost:8000/api/`
-   **Django Admin**: `http://localhost:8000/admin/`

---

## 5. Data Flow / Architecture

The system uses a decoupled, asynchronous architecture to handle potentially long-running tasks. This ensures the API remains responsive.

```mermaid
graph TD
    subgraph User Interaction
        A[Client/Frontend]
    end

    subgraph API Layer (Django/DRF)
        B[API View]
        C[Serializer]
        D[Model]
    end

    subgraph Task Queue
        E[Redis]
        F[Celery Worker]
    end

    subgraph External Services
        G[Amazon S3]
        H[PostgreSQL DB]
        I[OpenAI API]
    end

    A -- 1. HTTP Request --> B
    B -- 2. Validate with --> C
    C -- 3. Create/Update --> D
    D -- 4. Write to --> H
    B -- 5. Dispatch Task --> E
    F -- 6. Consume Task --> E
    F -- 7. Read/Write Files --> G
    F -- 8. Read/Write Data --> H
    F -- 9. Call for Generation --> I
    B -- 10. HTTP 202 Accepted --> A
```

**Typical Workflow (Content Generation):**
1.  A user sends a `POST` request to an endpoint like `/api/projects/{id}/generate_content/`.
2.  The DRF **View** (`ProjectViewSet`) receives the request.
3.  The corresponding **Serializer** validates the incoming data (e.g., `content_type`).
4.  The View creates a `GeneratedContent` **Model** instance with a `PENDING` status and saves it to the **PostgreSQL DB**.
5.  The View dispatches a Celery task (`generate_content_task`) to the **Redis** message broker.
6.  The API immediately returns a `202 Accepted` response to the user, indicating the task has been queued.
7.  A **Celery Worker** (running in a separate container) picks up the task from Redis.
8.  The worker executes the task logic from `projects/tasks.py`:
    -   Downloads the source file from **Amazon S3**.
    -   Processes the file and calls the **OpenAI API**.
    -   Uploads the newly generated file back to **S3**.
    -   Updates the `GeneratedContent` model's status to `SUCCESS` in the **PostgreSQL DB**.

---

## 6. Database Design

The core database schema revolves around Users, Projects, and the Content generated for them.

-   **User** (from `django.contrib.auth`): Standard Django user model for authentication.
-   **UserProfile** (`users.models`): A one-to-one relationship with `User` to store application-specific data like `token_balance`.
-   **Project** (`projects.models`): The central object. It belongs to a `User` and holds information about the source document (e.g., `name`, `s3_file_key`).
-   **GeneratedContent** (`projects.models`): Represents a piece of content (like a presentation or podcast) generated for a `Project`. It has a foreign key to `Project` and stores its own status (`task_status`), type, and final `s3_url`.

**Relationships:**
-   `User` 1-to-1 `UserProfile`
-   `User` 1-to-many `Project`
-   `Project` 1-to-many `GeneratedContent`

---

## 7. API Documentation

**Note**: This project does not yet have an automated Swagger/OpenAPI interface. Adding one (e.g., with `drf-spectacular`) is a high-priority improvement.

All endpoints are prefixed with `/api/` and require an `Authorization: Bearer <JWT>` header unless otherwise noted.

### User & Auth

-   **GET /api/users/me/**
    -   **Description**: Retrieves the profile for the currently authenticated user.
    -   **cURL**: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me/`
    -   **Sample Response**:
        ```json
        {
          "user": { "id": 1, "username": "dev", "email": "dev@example.com" },
          "token_balance": 100.0
        }
        ```

### Projects

-   **POST /api/projects/upload_file/**
    -   **Description**: Uploads a file to S3.
    -   **cURL**: `curl -X POST -H "Authorization: Bearer <token>" -F "file=@/path/to/doc.pdf" http://localhost:8000/api/projects/upload_file/`

-   **POST /api/projects/**
    -   **Description**: Creates a new project record using a pre-uploaded file.
    -   **cURL**: `curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"name": "My Notes", "s3_file_key": "uploads/1/doc.pdf"}' http://localhost:8000/api/projects/`

-   **GET /api/projects/**
    -   **Description**: Lists all projects for the current user.
    -   **cURL**: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/projects/`

### Content Generation

-   **POST /api/projects/{project_id}/generate_content/**
    -   **Description**: Starts an asynchronous job to generate content.
    -   **cURL**: `curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"content_type": "PRESENTATION", "num_slides": 10}' http://localhost:8000/api/projects/1/generate_content/`
    -   **Sample Response**:
        ```json
        {
          "message": "Content generation for 'PRESENTATION' started.",
          "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "content_id": 5
        }
        ```

-   **GET /api/content/{content_id}/**
    -   **Description**: Poll this endpoint to check the status of a generation task.
    -   **cURL**: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/content/5/`

---

## 8. Testing

The project is set up for testing with Django's built-in test framework.

**To run all tests:**
Execute the `test` command inside the `app` container.
```bash
docker-compose exec app python manage.py test
```

**Note**: The test suite is currently minimal. A key area for contribution is to add comprehensive unit and integration tests for all applications.

---

## 9. Linting & Formatting

To maintain code quality and consistency, we recommend using `black` for formatting and `flake8` for linting.

**To format the code:**
```bash
docker-compose exec app black .
```

**To check for linting errors:**
```bash
docker-compose exec app flake8 .
```

---

## 10. CI/CD Pipeline

**Status**: Not yet implemented.

A CI/CD pipeline is a critical area for improvement. A recommended approach would be to use **GitHub Actions**. A typical workflow would include:
1.  **Trigger**: On push to `main` or on pull request.
2.  **Jobs**:
    -   **Lint & Format Check**: Run `black --check .` and `flake8 .`.
    -   **Run Tests**: Execute `python manage.py test`.
    -   **Build Docker Image**: Build the production Docker image.
    -   **(Optional) Deploy**: On a successful merge to `main`, automatically deploy the new image to a staging or production environment.

---

## 11. Deployment Guide

The provided `docker-compose.yml` is for **local development only**.

For a production environment on AWS, a more robust architecture is recommended:
-   **Compute**: AWS ECS or Fargate to run the `app` and `celery_worker` containers.
-   **Database**: Amazon RDS for PostgreSQL for a managed, scalable database.
-   **Message Broker**: Amazon ElastiCache for Redis.
-   **File Storage**: Amazon S3 (as already configured).
-   **CI/CD**: A pipeline (see section 10) to automate deployments to this infrastructure.

---

## 12. Security & Secrets

-   **Secret Management**: All secrets (API keys, database passwords, Django secret key) **must** be stored in the `.env` file locally and as environment variables in production. **Never commit the `.env` file to version control.**
-   **IAM Roles**: In a production AWS environment, use IAM Roles attached to the ECS tasks instead of hardcoding `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as environment variables. This is significantly more secure.
-   **Debugging**: Ensure `DJANGO_DEBUG` is set to `False` in any production environment.

---

## 13. Common Issues / FAQ

-   **Celery worker doesn't start or pick up tasks:**
    -   Check that Redis is running: `docker-compose ps`.
    -   View worker logs for errors: `docker-compose logs celery_worker`.
-   **S3 Upload Fails:**
    -   Ensure your AWS credentials in `.env` are correct and have the necessary S3 permissions (`s3:PutObject`, `s3:GetObject`).
    -   Verify that the `AWS_STORAGE_BUCKET_NAME` exists and you have access to it.
-   **Migrations Fail:**
    -   This can happen if the database container didn't start correctly. Check its logs: `docker-compose logs db`.

---

## 14. Areas of Improvement

-   **Testing**: Build a comprehensive test suite with high coverage.
-   **CI/CD**: Implement a full CI/CD pipeline for automated testing and deployment.
-   **API Documentation**: Integrate `drf-spectacular` to generate a live OpenAPI/Swagger UI.
-   **Real-time Updates**: Replace polling with WebSockets (using Django Channels) for a better user experience.
-   **Error Handling**: Improve error reporting and implement retry mechanisms for Celery tasks.
-   **Frontend**: Develop a frontend application (e.g., React, Vue) to consume the API.

---

## 15. Versioning & Changelog

-   **Versioning**: This project should adhere to **Semantic Versioning (SemVer)**. Versions are tracked via Git tags (e.g., `v1.0.0`, `v1.1.0`).
-   **Changelog**: All significant changes should be documented in a `CHANGELOG.md` file (not yet created).
