# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src ./src

# Install package
RUN pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed package from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/src ./src

# Create data directory for database access
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run server
CMD ["python", "-m", "tree_analyzer_mcp.server"]
