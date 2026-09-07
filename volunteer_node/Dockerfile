FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch and node requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy volunteer client code
COPY . /app/volunteer_node

ENV PYTHONUNBUFFERED=1
ENV BROKER_SERVER="http://broker-server:8000"
ENV VOLUNTEER_TOKEN="NB_VOLUNTEER_SECRET_2026"

CMD ["python", "-m", "volunteer_node.main"]
