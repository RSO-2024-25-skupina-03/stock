import logging_loki

loki_handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"app": "stock-api"},
    version="1",
)
