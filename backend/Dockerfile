# 1. Base image
FROM python:3.13-slim

# 2. Set working directory
WORKDIR /app

# 3. Install uv
RUN pip install uv

# 4. Copy dependency files and install dependencies
COPY requirements.txt .
RUN uv pip install --no-cache --system -r requirements.txt

# 5. Copy application code and migrations
COPY ./app ./app
COPY alembic.ini .
COPY alembic ./alembic

# 6. Expose port and run application
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
