See the canonical upload-ready dataset card at
`../../HUGGINGFACE_DATASET_CARD.md`.

The upload helper builds an explicit data-only staging tree. It does not mirror
the GitHub repository. A dry run is the default:

```bash
python platforms/huggingface_dataset/upload_dataset.py
```

Preserve the exact candidate tree for inspection:

```bash
python platforms/huggingface_dataset/upload_dataset.py \
  --stage-dir ../releases/huggingface-core-stage
```

`--publish` opens a Hugging Face pull request that replaces the old remote
mirror with the staged dataset tree. Review and merge that request before
relying on the package's official download URL. Direct publication requires
the additional `--direct` flag.
