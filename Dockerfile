FROM python:3.11-slim

# Metadata (optional unless enforced)
LABEL org.opencontainers.image.title="ProPublica MCP Server" \
      org.opencontainers.image.description="MCP server providing access to ProPublica Nonprofit Explorer API for Form 990 data" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/asachs01/propublica-mcp"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up app directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md ./

# Install your package (assuming it's a poetry/setuptools package)
RUN pip install .

# Expose port
EXPOSE 8000

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('https://projects.propublica.org/nonprofits/api/v2/search.json?q=test', timeout=5)" || exit 1

# Default command
CMD ["python", "-m", "propublica_mcp.server"]
