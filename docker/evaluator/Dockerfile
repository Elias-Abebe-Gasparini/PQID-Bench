FROM python:3.13-slim

ARG QISKIT_VERSION=2.1.1
ARG QISKIT_AER_VERSION=0.17.0
ARG PYTHON_DATEUTIL_VERSION=2.9.0.post0

RUN python -m pip install --no-cache-dir \
    "qiskit==${QISKIT_VERSION}" \
    "qiskit-aer==${QISKIT_AER_VERSION}" \
    "python-dateutil==${PYTHON_DATEUTIL_VERSION}" \
    && python -c "import dateutil, qiskit, qiskit_aer"

WORKDIR /release
USER 65532:65532
ENTRYPOINT ["python", "/release/scripts/run_pqid_bench_external_model_generation_harness.py"]
