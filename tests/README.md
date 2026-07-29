# Test Tiers

The package uses three deliberately separate test tiers:

- `unit/`: synthetic records and isolated package behavior;
- `integration/`: representative end-to-end workflows against the release;
- `release_parity/`: exhaustive 3,234-cell and 4,536-cell scientific parity.

From a source checkout:

```bash
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/integration -v
python -m unittest discover -s tests/release_parity -v
```

The release-parity tier is mandatory before version tags and public artifacts.

The unit tier also exercises failure behavior for malformed JSONL, duplicate
model-prompt keys, conflicting endpoint aliases, incompatible run-manifest
versions, manifest corruption, and corrupted repeatability dimensions. The
integration tier verifies both full-denominator comparison and explicit
matched-subset comparison.
