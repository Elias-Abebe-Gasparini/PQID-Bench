# Glossary

## Artifact manifest

The TSV inventory recording each public release path, byte size, and SHA-256
digest.

## Archived replay

Re-execution of already collected generated programs under the named
evaluator. It does not call the model provider again.

## Assembly admissibility

The operational state \(A=1\): an executable selected circuit serializes
successfully to OpenQASM 3 under the evaluator. It does not denote execution
of the assembly on a simulator or hardware backend.

## AS-Gap

Assembly-Structure Gap. The aggregate contrast
\(\bar A-\bar M^{\mathrm{sig}}\). On the frozen release,
\(M^{\mathrm{sig}}\preceq A\), so it is the assembly-admissible subset of the
ES-Gap and counts \(A=1,M^{\mathrm{sig}}=0\) cells.

## Benchmark record

A source/governance row containing a stable row ID, instruction, and optional
reference program and release bucket.

## Benchmark release

The versioned prompt, split, target, and frozen scientific contract. It is
independent of package and evaluator versions.

## Candidate

One or more supplied model rows being summarized or compared with the frozen
benchmark.

## Canonical evaluation

One normalized scored model-prompt cell satisfying the package record and
endpoint invariants.

## Canonical response

The normalized provider/model response retained for one prompt, including
generated text/code or a normalized error.

## Cell

One `(model, prompt_id)` observation.

## Classical-bit count

The number of classical bits in the evaluated circuit, one component of the
reference signature.

## Complete matrix

The rectangular 21-model by 154-prompt frozen primary evaluation, containing
3,234 cells.

## Container artifact

The separately versioned image or archive used for isolated executable replay.
It encapsulates an evaluator contract but is not itself the evaluator version.

## Container image ID

The local content-addressed Docker image identity. It is distinct from the
archive SHA-256 and from an OCI registry manifest digest.

## Count map

A mapping from evaluator-visible operation type to multiplicity. It records
more information than the set of observed gate types.

## Denominator alignment

The requirement that candidate and comparator rates use the same prompt set.

## Deployment variation

Outcome variation caused by changing model services, routes, provider
infrastructure, policies, or serving systems.

## ERSD

Executable reference-signature disagreement rate. ES-Gap count divided by
execution count on the same cell set.

## ES-Gap

Execution-Structure Gap. The aggregate rate of cells that execute but fail the
frozen reference-signature predicate.

## Evaluation record

A canonical scored cell containing model, prompt, execution, signature,
optional assembly admissibility, and optional stricter reconstruction
endpoints.

## Evaluator

The versioned implementation that executes generated code, extracts circuit
descriptors, and computes evaluation endpoints.

## Executable output

Generated code that runs successfully under the named evaluator.

## Evidence bundle

The complete frozen public artifact directory containing records, analyses,
scripts, documentation, and the internal manifest. Manuscript-facing
publication derivatives are excluded.

## Frozen

Declared immutable for the named benchmark release.

## Gate vocabulary

The set of operation types present, without multiplicities. It must not be
used interchangeably with the complete operation-type count map.

## Identifiable prompt

A prompt whose wording uniquely specifies all components compared by the
frozen signature predicate.

## Matched-subset comparison

An explicit partial comparison in which frozen rows are restricted to the
candidate's exact prompt IDs.

## Model route

The evaluated combination of requested model, provider, and concrete serving
route represented by a canonical model label.

## Live replication

A newly identified, explicitly authorized model-provider run produced by
`run-model`. It is new stochastic evidence, not historical reproduction.

## Operation count

The scalar number of counted operations. Under the frozen predicate it follows
from complete count-map equality and is reported separately as a diagnostic.

## Ordered operation-and-operand tape

The sequence of operation names together with their quantum and classical
operands, compared in order.

## Parameter-aware match

An ordered match that additionally recovers the evaluator-normalized
parameter-value sequence.

## Predicate

The versioned rule determining whether an output passes a reconstruction
endpoint.

## Prompt ID

The stable identifier joining prompt, response, evaluation, and provider
attempt records.

## Provider attempt

One normalized request attempt, including route, model identities, timestamps,
status, hashes, usage, and error/transport metadata.

## QASM3 export

Successful export of an evaluated circuit to OpenQASM 3. It is a diagnostic
endpoint and is not equivalent to reference reconstruction.

## Qubit count

The number of qubits in the evaluated circuit, one component of the reference
signature.

## Reference signature

The frozen tuple operationalized by qubit count, classical-bit count, and the
complete operation-type count map.

## Replay

Execution of archived or newly collected generated code. In package version
1.2.0 it occurs only inside the isolated Docker evaluator.

## Replication

A new experiment, generally involving new model/provider calls and new run
identity.

## Reproduction

Deterministic reconstruction of published quantities from frozen evidence.

## Resolved model

The model identity reported or resolved by a provider, which may differ from
the requested alias.

## Run manifest

The seven-field version and run-type record attached to an experiment or
comparison.

## Schema

The machine-readable JSON record contract. Schema version is independent of
benchmark and evaluator versions.

## Semantic equivalence

Task-level or physical equivalence of circuit behavior. It is not established
by the frozen signature, ordered, or parameter-aware predicates.

## SHR

Structural-hallucination rate. The conditional frequency of \(E=1,M=0\) among
executable cells on the identifiable prompt subset.

## Structural hallucination

On an identifiable prompt, an executable output that fails the frozen
reference-signature predicate.

## Structural predicate

The explicitly limited reference-reconstruction rule used for signature
matching.

## Target signature

The frozen reference signature associated with a prompt's audited target
circuit.

## Transport affected

A provider-attempt flag indicating that network, service, quota, refusal, or
another transport/deployment condition affected observation.

## Trust boundary

The separation among local data processing, third-party network collection,
and generated-code execution.

## Version dimension

One independently recorded identity: package, benchmark, evaluator, predicate,
schema, artifact manifest, or run type.
