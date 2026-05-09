FROM python:3.11-slim

WORKDIR /app
COPY zap-annotation.py /app/zap-annotation.py

ENTRYPOINT ["python", "/app/zap-annotation.py"]
