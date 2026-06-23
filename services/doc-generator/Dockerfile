# Use official Python slim image - smaller attack surface for security
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user - never run containers as root in GxP environments
RUN groupadd -r gxpuser && useradd -r -g gxpuser gxpuser

# Copy and install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Change ownership to non-root user
RUN chown -R gxpuser:gxpuser /app

# Switch to non-root user
USER gxpuser

# Expose port
EXPOSE 8000

# Health check built into container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
