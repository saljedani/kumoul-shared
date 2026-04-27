FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create upload directory
RUN mkdir -p app/uploads instance

# Expose port
EXPOSE 5000

# Init DB then start
CMD ["sh", "-c", "python init_db.py; gunicorn -w 4 -b 0.0.0.0:5000 'run:app'"]
