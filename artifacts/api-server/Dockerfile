FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fpdf2

# Copy code
COPY . .

# Expose port and define default volumes for SQLite & ChromaDB
EXPOSE 8080
VOLUME ["/app/db"]

CMD ["python", "main.py"]
