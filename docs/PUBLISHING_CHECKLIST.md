# PQID-Bench v1.0.0 Publishing Checklist

This document records the release protocol used for the published, frozen
PQID-Bench v1.0.0 evidence object and the reusable checks for later software
releases. The `v1.0.0` benchmark tag and DOI are now public; unchecked items
remain verification prompts rather than statements that publication is
pending.

The local package is the single source for GitHub, Zenodo, and the Hugging
Face Dataset. The underlying PQID dataset remains a separate immutable release
(`10.5281/zenodo.20674853`). The PQID-Bench v1.0.0 archive DOI is
`10.5281/zenodo.21649753`.

## Python Package

- [ ] Confirm the `pqid-bench` project name is available on PyPI.
- [ ] Create the GitHub repository before configuring PyPI Trusted Publishing.
- [ ] Configure the PyPI Trusted Publisher for
      `.github/workflows/publish-pypi.yml` and environment `pypi`.
- [ ] Confirm public CI passes on Python 3.11, 3.12, 3.13, and 3.14.
- [ ] Run `.github/workflows/release-parity.yml` successfully.
- [ ] Confirm the mocked `run-model` suite passes without network access,
      including consent, secret non-persistence, retry, resume, terminal-error
      recovery, and uncertain in-flight recovery cases.
- [ ] Confirm `run-model --dry-run` neither reads credentials nor creates an
      output directory or contacts a provider.
- [ ] Confirm a mocked live response completes the
      `run-model -> replay -> evaluate -> compare` path and produces JSON,
      text, Markdown, and CSV summaries.
- [ ] Confirm the CI container job builds the pinned evaluator and imports
      Qiskit, Qiskit Aer, and python-dateutil at their recorded versions.
- [ ] Confirm `pqid-bench verify . --full` passes from an installed wheel.
- [ ] Install the final source distribution in a separate clean environment
      and confirm `pqid-bench reproduce --release-dir .` passes.
- [ ] Confirm the wheel contains all six versioned JSON Schemas.
- [ ] Publish through the GitHub release workflow; do not create a long-lived
      PyPI API token.
- [ ] Verify the PyPI wheel and source-distribution attestations.
- [ ] Attach or link the wheel, source distribution, and `SHA256SUMS.txt` from
      a newly generated DOI-complete staging directory under
      `releases/python/` in the GitHub release.

## 1. Local Freeze

- [ ] Run `python scripts/build_pqid_bench_public_release.py --archive` from
  the parent ACM TQC benchmark folder.
- [ ] Confirm `ARTIFACT_MANIFEST.tsv` has no missing or mismatched files.
- [ ] Confirm the release ZIP and `.sha256` sidecar exist under the parent
  `releases/` directory.
- [ ] Confirm the privacy scan reports no workstation paths or credential-file
  names.
- [ ] Confirm live-run manifests use release-relative or filename-only prompt
  references and that no credential value, credential-file path, or
  evaluator-only target metadata appears in persisted live-run artifacts.
- [ ] Confirm the release-scope validator rejects manuscript source, rendered
      publication outputs, copy-ready tables, notebooks, and Space bundles.
- [ ] Run `mkdocs build --strict` and archive the completed output.
- [ ] Generate and retain a software bill of materials.
- [ ] Record the final Git commit used for the `v1.0.0` tag.

## 2. GitHub Repository Bootstrap

Repository:

`https://github.com/Elias-Abebe-Gasparini/PQID-Bench`

- [ ] Create the repository without generating a competing README or license.
- [ ] Add this package directory as its working tree.
- [ ] Commit and push the verified release candidate to `main`.
- [ ] Confirm GitHub recognizes `CITATION.cff`.
- [ ] Do not create `v1.0.0` until the benchmark DOI has been reserved and
      embedded in every required surface.

Repository presentation:

- [ ] Set the repository homepage to the public documentation site.
- [ ] Apply the curated quantum-computing, benchmarking, evaluation, and
      reproducibility topics.
- [ ] Upload `.github/assets/pqid-bench-social-preview.png` under **Settings >
      General > Social preview**.
- [ ] Confirm the CI, DOI, PyPI, Python, GHCR, and documentation badges render.
- [ ] Confirm GitHub recognizes the contribution, conduct, security, support,
      issue-template, and pull-request-template files.

## 3. Zenodo DOI Reservation and Final Freeze

- [ ] Enable the GitHub repository in Zenodo, or create a direct software
      deposit draft.
- [ ] Reserve the benchmark version DOI without publishing the draft.
- [ ] Insert the reserved benchmark DOI into `CITATION.cff`, `README.md`,
      `HUGGINGFACE_DATASET_CARD.md`, and the manuscript artifact-availability
      statement.
- [ ] Keep `10.5281/zenodo.20674853` as the separate `isDerivedFrom` dataset
      DOI.
- [ ] Rerun the release builder, manifest validator, package tests, strict
      documentation build, distribution build, Twine check, and upload-plan
      dry runs.
- [ ] Regenerate the final checksums and artifact registry.
- [ ] Commit the DOI-complete, byte-final release and record its Git commit.

Do not substitute the source-dataset concept DOI
`10.5281/zenodo.20019482` for the benchmark DOI.

## 4. GitHub Release

- [ ] Create the annotated tag and release `v1.0.0` from the DOI-complete
      final commit.
- [ ] Attach `PQID-Bench-v1.0.0-frozen.zip` and its SHA-256 sidecar.
- [ ] Attach or link the wheel, source distribution, `SHA256SUMS.txt`, and
      both CycloneDX SBOMs.
- [ ] Verify that the public tag and release assets match the local hashes.
- [ ] Ask an independent user to complete the tiered workflow in
      `docs/REVIEWER_QUICKSTART.md` and retain their environment and command
      transcript.

## 5. Zenodo Publication

- [ ] Use `.zenodo.json` and `ZENODO_METADATA.md`.
- [ ] Upload the exact DOI-complete frozen ZIP, checksum sidecar, software
      distributions, and SBOMs registered above.
- [ ] Publish the reserved draft.
- [ ] Record both the benchmark version DOI and benchmark concept DOI.
- [ ] Verify that downloaded Zenodo bytes match the local release checksums.

### DOI-Preserving Metadata Corrections

A reader-facing clarification to title, description, keywords, or related
identifiers is a metadata correction, not a new benchmark release. Keep the
version DOI and all deposited files unchanged.

- [ ] Edit the published record rather than creating a new version.
- [ ] Source the replacement fields from `.zenodo.json`.
- [ ] Use the maintainer publisher's `--metadata-only` mode; never combine it
      with `--sync`.
- [ ] Require a zero-difference comparison between the complete local and
      remote file inventories before writing metadata.
- [ ] Verify the same filename, byte count, and checksum inventory after the
      metadata update and again after republishing the record.
- [ ] Confirm that the public record explains the materialized split files,
      `E`, `A`, `M^sig`, ES-Gap, AS-Gap, the current `pqid-bench` package, and
      the independent benchmark/package/evaluator/predicate version numbers.

Any change to benchmark rows, split membership, canonical responses, scoring
behavior, or frozen analytical evidence requires a new versioned deposit.

## 6. Hugging Face Dataset

Repository:

`https://huggingface.co/datasets/Elias-Abebe-Gasparini/PQID-Bench`

Dry-run the upload plan:

```powershell
python ".\platforms\huggingface_dataset\upload_dataset.py"
```

Publish only after the GitHub release is visible:

```powershell
python ".\platforms\huggingface_dataset\upload_dataset.py" --publish
```

- [ ] Confirm the root card is `HUGGINGFACE_DATASET_CARD.md`.
- [ ] Confirm the `clean_generation` configuration exposes 734 rows.
- [ ] Confirm the card reports `21 x 154`, not the superseded `15 x 70` pilot.
- [ ] Confirm repository links and the source dataset DOI resolve.

## 7. Container Publication

- [ ] Confirm the container archive SHA-256 matches
      `releases/docker/final-pre-doi/container-image-metadata.json`. The
      validated image contains no DOI-bearing metadata and therefore does not
      require a binary rebuild after DOI reservation.
- [x] Publish
      `ghcr.io/elias-abebe-gasparini/pqid-bench-evaluator:1.0.0` through
      `.github/workflows/publish-ghcr.yml`.
- [x] Record immutable OCI registry manifest digest
      `sha256:39825f5635cd6273e9e23c2848f2c88a2ff9d461e16a263fd89f22c6e664ac8f`
      separately from the local Docker image ID and archive SHA-256.
- [x] Verify that the published image encapsulates evaluator
      `pqid-bench-evaluator-1.1.0-safe-builtins`.

## 8. Cross-Platform Audit

- [ ] Version is `v1.0.0` everywhere.
- [ ] Scientific freeze is `2026-07-23`.
- [ ] Primary matrix is 3,234 cells (`21 x 154`).
- [ ] Execution is 91.22%; assembly admissibility is 91.03%; signature
      recovery is 52.66%; ES-Gap is 38.56 pp; AS-Gap is 38.37 pp.
- [ ] Source dataset version DOI is `10.5281/zenodo.20674853`.
- [ ] Source dataset concept DOI is `10.5281/zenodo.20019482`.
- [ ] Benchmark DOI is `10.5281/zenodo.21649753` across every DOI-bearing
      surface.
- [ ] Archive SHA-256 agrees with the release sidecar.
- [ ] Public GitHub, Hugging Face, and Zenodo inventories contain no
      manuscript-facing publication derivative.
- [ ] An independent user has completed the reviewer quickstart and the
  environment and command transcript has been retained.
