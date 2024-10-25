FROM python:3.11-alpine

RUN pip install --no-cache-dir fastapi pymongo uvicorn
COPY src/stock /app/

EXPOSE 8080

WORKDIR /app
CMD ["python3", "api.py"]
