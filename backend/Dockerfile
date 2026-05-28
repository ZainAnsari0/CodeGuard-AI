FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy application code
COPY . .

# Ensure appuser owns all application files
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Run the application (production — no --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]