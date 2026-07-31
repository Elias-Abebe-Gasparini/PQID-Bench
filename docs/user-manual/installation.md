# Installation

## 1. Requirements

The metric and integrity layer requires:

- Python 3.11, 3.12, 3.13, or 3.14;
- the `pqid-bench` wheel, source distribution, or source checkout; and
- an extracted PQID-Bench distribution: the compact core for new benchmark
  runs, or the complete evidence archive for published-result reproduction.

Docker Engine is optional. It is required only for `replay`.
Network access and a provider credential are required only for an actual
`run-model` call; `run-model --dry-run` requires neither.
The dependency-free package core is tested on Python 3.11--3.14. The frozen
Docker evaluator intentionally remains on Python 3.13 with Qiskit 2.1.1 and
Qiskit Aer 0.17.0; its runtime is a separate reproducibility contract rather
than the package-core compatibility range.

The core Python package has no mandatory third-party runtime dependency.
Optional JSON Schema and host-side evaluator dependencies are declared
separately in `pyproject.toml`. Plotly is optional and is required only to
generate the interactive explorer.

## 2. Obtain The Distribution Objects

The frozen benchmark and the current software package are distributed as
separate objects:

| Object | Purpose |
| --- | --- |
| `PQID-Bench-v1.0.0-core.zip` | compact benchmark-user distribution |
| `PQID-Bench-v1.0.0-frozen.zip` | complete frozen evidence and study-reproduction archive |
| `pqid-bench 1.2.1` | current installable acquisition, evaluation, and reporting interface |
| `pqid_bench-1.0.0-py3-none-any.whl` | original package wheel preserved with the evidence freeze |
| `pqid_bench-1.0.0.tar.gz` | original package source distribution preserved with the evidence freeze |

The optional evaluator image is distributed separately as
`pqid-bench-evaluator-1.0.0-linux-amd64.tar.gz`.

Installing the wheel does not silently install benchmark data. Use
`pqid-bench download` for the compact authenticated distribution, or obtain
the complete evidence archive from Zenodo. Pass the resulting directory
explicitly with `--release-dir`.

## 3. Verify Downloaded Files

Compare downloaded files with the published SHA-256 sidecars before
installation.

On Linux or macOS:

```bash
sha256sum -c SHA256SUMS.txt
```

On PowerShell, for the original files preserved with the frozen release:

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

Install the current package from PyPI:

```bash
python -m pip install pqid-bench==1.2.1
```

From a locally built current wheel:

```bash
python -m pip install pqid_bench-1.2.1-py3-none-any.whl
```

From a source checkout:

```bash
python -m pip install .
```

For exact software-level reconstruction of the original frozen environment,
the archived `1.0.0` wheel remains installable:

```bash
python -m pip install pqid_bench-1.0.0-py3-none-any.whl
```

All package versions implement the same benchmark `1.0.0`, evaluator,
predicate, and schema contracts. Package `1.2.1` includes authenticated core
acquisition without changing a frozen score.

## 6. Optional Dependencies

Install JSON Schema validation support:

```bash
python -m pip install "pqid-bench[schema]==1.2.1"
```

Install the host-side evaluator-compatible scientific stack:

```bash
python -m pip install "pqid-bench[evaluator]==1.2.1"
```

The evaluator extra is not required for Docker replay. The Docker image pins
its own Qiskit environment.

Install standalone interactive reporting:

```bash
python -m pip install "pqid-bench[visualization]==1.2.1"
```

Install the documentation and visualization toolchain from a source checkout:

```bash
python -m pip install -e ".[docs]"
```

For local package development:

```bash
python -m pip install -e ".[dev]"
```

## 7. Acquire And Identify A Release Directory

For benchmark use, download and verify the compact distribution:

```bash
pqid-bench download --version 1.0.0
```

The JSON result reports `release_dir`, `archive_path`, the pinned SHA-256,
manifest-entry count, and whether the release was newly downloaded or reused.
Set `PQID_BENCH_CACHE_DIR` to override the default user cache. To use a custom
mirror, supply both `--url` and `--sha256`.

For full study reproduction, extract `PQID-Bench-v1.0.0-frozen.zip` from the
Zenodo evidence record instead. Both profiles contain:

```text
ARTIFACT_MANIFEST.tsv
artifacts/
data/
docker/
scripts/
```

The compact profile supports `verify`, `run-model`, `replay`, and `evaluate`.
The complete evidence profile additionally supports `reproduce`, `compare`,
`dashboard`, and `verify --full`.

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
pqid-bench 1.2.1
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

Pull the public evaluator image from GitHub Packages and assign the frozen
local tag expected by `pqid-bench replay`:

```bash
docker pull ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0
docker tag \
  ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0 \
  pqid-bench-evaluator:1.0.0
```

For an offline installation, load the image archive included with the complete
scientific release:

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
| public package | `ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0` |
| local image ID | `sha256:849bf53e449fd618633199c0b622abeca270591dff248cd0bf3a0fd461abf2e2` |
| archive SHA-256 | `8abff46dcb1fa10f375a713d94845d2b0bdb3cd7601985ee6ef2da24dfdc09ba` |
| evaluator version | `pqid-bench-evaluator-1.1.0-safe-builtins` |
| OCI registry manifest digest | `sha256:39825f5635cd6273e9e23c2848f2c88a2ff9d461e16a263fd89f22c6e664ac8f` |

The local image ID is not a substitute for a registry manifest digest. Record
the OCI digest when citing or pinning the public package.

The published archive targets Linux containers on `amd64`. Docker Desktop can
run that Linux image on supported Windows installations.

## 10. Uninstall

```bash
python -m pip uninstall pqid-bench
```

Uninstalling the Python package does not delete the separately extracted
evidence bundle, downloaded distributions, or Docker image.
