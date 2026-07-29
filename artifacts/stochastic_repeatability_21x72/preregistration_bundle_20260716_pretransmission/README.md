# PQID-Bench 72-Prompt Repeatability Preregistration Bundle

This bundle was sealed at `2026-07-15T15:20:39+00:00` before any live response, raw provider
output, evaluation artifact, or process log existed for augmentation Runs 2
and 3. It cryptographically records the outcome-blind 36-prompt confirmatory
panel that extends the original 36-prompt audit to 72 prompts.

## Frozen Design

- 21 model routes;
- 36 original prompts plus 36 signature-disjoint confirmatory prompts;
- 72 unique reference signatures and no identifiability exceptions;
- 18 pilot and 18 extension prompts in the added panel;
- 12 added prompts in each gate-type bin;
- 1,512 new logical calls and 4,536 pooled run-level outputs when complete.

The added `3 x 2` allocation is `7/5`, `6/6`, and `5/7` across the `1-2`,
`3-4`, and `5+` gate-type rows. Exact `6/6` balance is infeasible because the
remaining eligible pool contains only five pilot signatures in the `5+` row.
The eligible-pool snapshot contains `104` remaining unique-signature
representatives and all collapsed prompt-member IDs.

## Evidential Order

1. original 36-prompt audit;
2. new 36-prompt confirmatory replication;
3. pooled 72-prompt precision analysis;
4. complete deployment and transport-unaffected estimates reported separately.

## Integrity

`SHA256SUMS.txt` hashes every file in this directory except itself. The sibling
ZIP archive has a separate `.sha256` seal. The frozen augmentation protocol
hash at bundle creation is `5c5761626fab260882fa41dc0a469570db17bdeedf9d785754a8c7329727df47`. API credentials are deliberately
excluded.
