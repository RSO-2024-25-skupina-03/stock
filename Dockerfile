FROM python:3.11-alpine

RUN pip install --no-cache-dir pdm
COPY src/stock /app/src/stock
COPY pdm.lock /app
COPY pyproject.toml /app

WORKDIR /app/src/stock
RUN pdm install --check --prod --no-editable

EXPOSE 8080

CMD ["pdm", "run", "python3", "-m", "api"]
