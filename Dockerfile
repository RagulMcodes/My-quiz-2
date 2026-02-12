FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements_llm.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements_llm.txt

# Copy server code
COPY quiz_server_production.py .

# Copy .env if it exists (optional - better to use env vars)
COPY .env* ./

# Expose port (will be overridden by cloud platform's PORT env var)
EXPOSE 8765

# Run the server
CMD ["python", "quiz_server_production.py"]
