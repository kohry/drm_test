# 1. Base image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# 3. Set working directory
WORKDIR /app

# 4. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy source code
COPY server.py .

# 6. Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

# 7. Run application
CMD ["python", "server.py"]
