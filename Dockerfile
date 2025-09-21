FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y build-essential --no-install-recommends && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential
CMD ["python", "main.py"]