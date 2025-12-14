FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8765

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
