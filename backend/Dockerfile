FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies (install globally as root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user (after installing packages so they're accessible)
RUN useradd -m -u 1000 app && \
    chown -R app:app /app

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user (packages installed globally are still accessible)
USER app

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

