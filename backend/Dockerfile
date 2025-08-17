FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir uv
RUN uv pip install --system .

# Copy application code
COPY . .

# Make entrypoint script executable (ensure it has proper permissions)
RUN chmod +x ./entrypoint.sh

# Expose the port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]
