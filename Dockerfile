FROM python:3.13.1-slim

COPY . /arq_http
WORKDIR /arq_http

RUN pip3 install .

RUN useradd -U arqhttp \
    && chown -R arqhttp:arqhttp /arq_http
USER arqhttp

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
    "arq_http.server:app" \
]
