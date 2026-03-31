FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and .env file
COPY okta_password_hash.py .
COPY okta_password_hash_twc_sha1.py .
COPY .env .

# Default: run the SHA-1 authentication script
# Override with: docker run -it okta-password-hash python okta_password_hash.py
CMD ["python", "okta_password_hash_twc_sha1.py"]
