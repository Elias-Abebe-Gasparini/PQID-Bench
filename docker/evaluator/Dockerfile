FROM python:3.13-slim

ARG QISKIT_VERSION=2.1.1
ARG QISKIT_AER_VERSION=0.17.0
ARG PYTHON_DATEUTIL_VERSION=2.9.0.post0
ARG IMAGE_VERSION=1.0.0

LABEL org.opencontainers.image.title="PQID-Bench evaluator"
LABEL org.opencontainers.image.description="Pinned, isolated runtime for PQID-Bench executable replay"
LABEL org.opencontainers.image.source="https://github.com/Elias-Abebe-Gasparini/PQID-Bench"
LABEL org.opencontainers.image.documentation="https://elias-abebe-gasparini.github.io/PQID-Bench/"
LABEL org.opencontainers.image.url="https://github.com/Elias-Abebe-Gasparini/PQID-Bench/pkgs/container/pqid-bench-evaluator"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="${IMAGE_VERSION}"

RUN python -m pip install --no-cache-dir \
    "qiskit==${QISKIT_VERSION}" \
    "qiskit-aer==${QISKIT_AER_VERSION}" \
    "python-dateutil==${PYTHON_DATEUTIL_VERSION}" \
    && python -c "import dateutil, qiskit, qiskit_aer"

WORKDIR /release
USER 65532:65532
ENTRYPOINT ["python", "/release/scripts/run_pqid_bench_external_model_generation_harness.py"]
