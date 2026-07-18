FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data/incoming /data/incoming_drafts /data/training/images /data/training/masks /data/rejected
EXPOSE 8501
CMD ["python", "-m", "platform.client.agent"]
