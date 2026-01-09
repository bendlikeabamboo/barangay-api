FROM python:3.12-slim

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install .

# Expose obscure port
EXPOSE 48573

# Run the application
CMD ["uvicorn", "barangay_api.main:app", "--host", "0.0.0.0", "--port", "48573"]