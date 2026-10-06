# python:3.11.9-slim-bookworm e espressif/idf:v5.4.2, fixados por digest.
FROM python@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317 AS python311
FROM espressif/idf@sha256:4317595a911886e04cbc6d731315d5fc2918e510b6733fc7d03381ab2d270082

# Python do ML separado do Python e dos pacotes internos do ESP-IDF.
COPY --from=python311 /usr/local/ /opt/python311/
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 libbz2-1.0 libreadline8t64 libffi8 liblzma5 \
    libgdbm6t64 libgdbm-compat4t64 libncursesw6 libexpat1 zlib1g \
    && rm -rf /var/lib/apt/lists/*
RUN /opt/python311/bin/python3.11 -m venv /opt/har-venv
COPY requirements.txt requirements-dev.txt requirements-lock-linux.txt /tmp/har-requirements/
RUN /opt/har-venv/bin/python -m pip install --no-cache-dir \
    -r /tmp/har-requirements/requirements-dev.txt \
    -r /tmp/har-requirements/requirements-lock-linux.txt \
    && /opt/har-venv/bin/python -m pip check

# Um processo separado ativa o SDK; Python/ML continua usando seu proprio venv.
COPY .devcontainer/idf-wrapper.sh /usr/local/bin/idf.py
RUN chmod +x /usr/local/bin/idf.py \
    && git config --system --add safe.directory /workspaces/tinyml-har
ENV PATH="/opt/har-venv/bin:${PATH}" \
    IDF_TARGET=esp32s3 \
    IDF_CCACHE_ENABLE=0 \
    PYTHONUTF8=1
WORKDIR /workspaces/tinyml-har
# export.sh no entrypoint original alteraria o Python padrao do ML.
ENTRYPOINT []
CMD ["sleep", "infinity"]
