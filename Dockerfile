FROM python:3.11-alpine

RUN pip install --no-cache-dir pdm
COPY src/rso_stock /app/src/rso_stock
COPY pdm.lock /app
COPY pyproject.toml /app

WORKDIR /app/
RUN pdm install --check --prod --no-editable

EXPOSE 8080

CMD ["pdm", "api"]
