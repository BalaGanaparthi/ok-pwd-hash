FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and .env file
COPY okta_password_hash.py .
COPY .env .

# Run the application
CMD ["python", "okta_password_hash.py"]
