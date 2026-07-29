# Installation

## 1. Requirements

The metric and integrity layer requires:

- Python 3.11, 3.12, 3.13, or 3.14;
- the `pqid-bench` wheel, source distribution, or source checkout; and
- the extracted PQID-Bench frozen evidence bundle for `verify`, `reproduce`,
  `compare`, and release-backed replay.

Docker Engine is optional. It is required only for `replay`.
Network access and a provider credential are required only for an actual
`run-model` call; `run-model --dry-run` requires neither.
The dependency-free package core is tested on Python 3.11--3.14. The frozen
Docker evaluator intentionally remains on Python 3.13 with Qiskit 2.1.1 and
Qiskit Aer 0.17.0; its runtime is a separate reproducibility contract rather
than the package-core compatibility range.

The core Python package has no mandatory third-party runtime dependency.
Optional JSON Schema and host-side evaluator dependencies are declared
separately in `pyproject.toml`.

## 2. Obtain The Distribution Objects

The release has three separate objects:

| Object | Purpose |
| --- | --- |
| `PQID-Bench-v1.0.0-frozen.zip` | complete frozen evidence bundle |
| `pqid_bench-1.0.0-py3-none-any.whl` | installable Python interface |
| `pqid_bench-1.0.0.tar.gz` | package source distribution |

The optional evaluator image is distributed separately as
`pqid-bench-evaluator-1.0.0-linux-amd64.tar.gz`.

Installing the wheel does not install the approximately 160 MB evidence
bundle. Keep the extracted release directory and pass it explicitly with
`--release-dir`.

## 3. Verify Downloaded Files

Compare downloaded files with the published SHA-256 sidecars before
installation.

On Linux or macOS:

```bash
sha256sum -c SHA256SUMS.txt
```

On PowerShell:

```powershell
Get-FileHash .\pqid_bench-1.0.0-py3-none-any.whl -Algorithm SHA256
Get-FileHash .\pqid_bench-1.0.0.tar.gz -Algorithm SHA256
```

The release checksum proves file identity. It does not replace the internal
manifest and scientific parity checks described below.

## 4. Create A Virtual Environment

On Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

On PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Using a virtual environment is recommended so the package installation is
separate from scientific host environments.

## 5. Install The Package

From the wheel:

```bash
python -m pip install pqid_bench-1.0.0-py3-none-any.whl
```

From the source distribution:

```bash
python -m pip install pqid_bench-1.0.0.tar.gz
```

From a source checkout:

```bash
python -m pip install .
```

After a public PyPI release, the equivalent registry installation is:

```bash
python -m pip install pqid-bench==1.0.0
```

Do not treat that command as available until the package is actually
published.

## 6. Optional Dependencies

Install JSON Schema validation support:

```bash
python -m pip install "pqid-bench[schema]==1.0.0"
```

Install the host-side evaluator-compatible scientific stack:

```bash
python -m pip install "pqid-bench[evaluator]==1.0.0"
```

The evaluator extra is not required for Docker replay. The Docker image pins
its own Qiskit environment.

For local package development:

```bash
python -m pip install -e ".[dev]"
```

## 7. Extract And Identify The Release Directory

Extract `PQID-Bench-v1.0.0-frozen.zip`. The resulting directory should contain:

```text
ARTIFACT_MANIFEST.tsv
artifacts/
data/
docker/
scripts/
```

Set `RELEASE_DIR` to that directory.

On Linux or macOS:

```bash
export RELEASE_DIR="/path/to/PQID-Bench-v1.0.0"
```

On PowerShell:

```powershell
$env:RELEASE_DIR = "C:\path\to\PQID-Bench-v1.0.0"
```

## 8. Confirm The Installation

```bash
pqid-bench --version
pqid-bench doctor
pqid-bench verify "$RELEASE_DIR"
```

Expected package version:

```text
pqid-bench 1.0.0
```

Expected integrity result:

```json
{
  "valid": true
}
```

`doctor` may report that Docker or optional packages are unavailable. That is
not an installation failure unless the intended workflow requires them.

## 9. Install Or Load The Docker Evaluator

Start Docker Engine before using replay.

To load the published image:

```bash
docker load --input pqid-bench-evaluator-1.0.0-linux-amd64.tar.gz
```

To build the image from the extracted release instead, pass `--build-image`
to `pqid-bench replay`. The image tag is
`pqid-bench-evaluator:1.0.0`.

The replay distribution has a separate identity from the evaluator contract:

| field | frozen local value |
| --- | --- |
| container artifact version | `1.0.0` |
| image tag | `pqid-bench-evaluator:1.0.0` |
| local image ID | `sha256:849bf53e449fd618633199c0b622abeca270591dff248cd0bf3a0fd461abf2e2` |
| archive SHA-256 | `8abff46dcb1fa10f375a713d94845d2b0bdb3cd7601985ee6ef2da24dfdc09ba` |
| evaluator version | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| OCI registry manifest digest | pending publication |

The local image ID is not a substitute for a registry manifest digest. Record
the OCI digest only after the image is published.

The published archive targets Linux containers on `amd64`. Docker Desktop can
run that Linux image on supported Windows installations.

## 10. Uninstall

```bash
python -m pip uninstall pqid-bench
```

Uninstalling the Python package does not delete the separately extracted
evidence bundle, downloaded distributions, or Docker image.
