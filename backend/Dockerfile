# Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install system dependencies (for PostgreSQL client)
RUN apt-get update && apt-get install -y postgresql-client

# 5. Install Python dependencies
# Copy the requirements file first to leverage Docker's caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your application code into the container
COPY . .

# 7. Expose the port the app runs on
EXPOSE 8000