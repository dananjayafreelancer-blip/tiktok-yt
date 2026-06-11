FROM python:3.10-slim

# FFmpeg සහ අවශ්‍ය Tools බැක්ඇන්ඩ් එකට ඉන්ස්ටෝල් කිරීම
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render එකේ සර්වර් එක Run කරන Command එක
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
