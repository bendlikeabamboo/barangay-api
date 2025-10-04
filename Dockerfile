FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only requirements to cache dependencies
COPY pyproject.toml poetry.lock ./

# Copy application code
COPY . .

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Expose obscure port
EXPOSE 48573

# Run the application
CMD ["uvicorn", "barangay_api.main:app", "--host", "0.0.0.0", "--port", "48573"]