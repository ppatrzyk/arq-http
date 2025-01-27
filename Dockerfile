FROM python:3.13.1-slim

COPY . /arq_monitor
WORKDIR /arq_monitor

RUN pip3 install .

RUN useradd -U arqmonitor \
    && chown -R arqmonitor:arqmonitor /arq_monitor
USER arqmonitor

EXPOSE 8000

CMD [ \
    "uvicorn", \
    "--host", \
    "0.0.0.0", \
    "--port", \
    "8000", \
    "--workers", \
    "1", \
    "--timeout-graceful-shutdown", \
    "1", \
    "arq_monitor.server:app" \
]
