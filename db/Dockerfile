FROM postgres:alpine

RUN apk add --no-cache --virtual .build-deps \
    python3 \
    py3-pip \
    libpq-dev \
    gcc

RUN pip install --no-cache-dir psycopg2-binary pyyaml

WORKDIR script

COPY . .

ENTRYPOINT ["python3", "./install.py"]
