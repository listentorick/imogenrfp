FROM python:3.11

WORKDIR /app

# Install system dependencies for ChromaDB 1.0.15
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    cmake \
    libmagic1 \
    libhdf5-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools for better dependency resolution
RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]