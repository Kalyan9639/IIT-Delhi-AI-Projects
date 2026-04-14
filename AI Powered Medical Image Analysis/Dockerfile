# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV (required for gradcam.py)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (use --no-cache-dir to save space)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Cloud Run uses the PORT environment variable (default 8080)
ENV PORT=8080

# Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
