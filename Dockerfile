# Offline verification image. Build once with network; run with --network none.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
# Limits suggested by the task: 2 CPU, 4 GB RAM, no GPU:
#   docker run --rm --network none --cpus 2 --memory 4g auditforge
CMD ["make", "verify"]
