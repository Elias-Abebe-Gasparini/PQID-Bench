# PQID-Bench Repeatability Protocol Amendments

## Amendment 1: Implementation-Audit Corrections

Finalized at `2026-07-15T19:16:40+09:00`.

An independent implementation review was requested without access to the live
repeatability outcomes. The review began while Run 3 collection was underway.
The user-launched master process completed Run 3 and generated preliminary
analysis artifacts before all corrections below were finalized. Those
preliminary artifacts were not inspected for scientific results and are
invalidated. They must be overwritten by the hash-locked analyzer after the
corrected null and adversarial tests pass. API response logs remain frozen and
are not regenerated or selected by outcome.

The amendments are methodological and outcome-independent:

1. Replaced the covariance-pseudoinverse joint Wald test with an empirical
   centered crossed-bootstrap L2 test that remains defined under singular
   covariance.
2. Reclassified the former post-stratified result as a gate-bin-standardized
   panel sensitivity. It is not an unbiased estimate of the full 154-prompt
   population.
3. Added hard-coded panel-file hash verification and exact hidden-target
   metadata checks for every scored cell.
4. Clarified that crossed uncertainty is conditional on the three observed run
   occasions and does not estimate future-date or deployment-shock variance.
5. Changed missing transport histories to explicit null/unknown values and
   strengthened the definition of attempt-trace coverage.
6. Rejected duplicate prompt IDs in response logs instead of silently applying
   last-row-wins canonicalization.
7. Defined the majority-vote ES-Gap as `E^maj - M^maj`; a direct majority vote
   over runwise `R` remains a separately labeled diagnostic.
8. Added cryptographic enforcement of the final protocol and amendment hashes.

No benchmark prompt, provider response, target signature, evaluator predicate,
model roster, or panel membership changed in this amendment.

