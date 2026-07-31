# Software Bills Of Materials

The release keeps separate CycloneDX inventories for its two software
boundaries:

- `pqid-bench-python-1.2.1.cdx.json` describes the current dependency-free core
  Python package declared by `pyproject.toml` and
  `requirements/package-runtime.txt`.
- `pqid-bench-python-1.2.0.cdx.json` preserves the preceding package SBOM.
- `pqid-bench-evaluator-1.0.0.cdx.json` describes the optional isolated
  executable-replay environment declared by
  `requirements/evaluator-container.txt`.

Both files use CycloneDX 1.6 JSON and reproducible-output mode. The broader
analysis stack in the root `requirements.txt` supports regenerating research
figures and analyses but is not installed by the `pqid-bench` Python package.
