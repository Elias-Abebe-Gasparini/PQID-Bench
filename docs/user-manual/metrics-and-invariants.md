# Metrics And Invariants

## 1. Notation

Let:

- \(F\) be a set of model rows;
- \(S\) be a prompt set;
- \(N=|F||S|\) be the number of model-prompt cells;
- \(E_i(f)\) indicate evaluator execution success;
- \(A_i(f)\) indicate quantum-assembly admissibility through successful
  OpenQASM 3 serialization;
- \(M_i^{\mathrm{sig}}(f)\) indicate reference-signature recovery;
- \(M_i^{\mathrm{ord}}(f)\) indicate ordered operation-and-operand recovery; and
- \(M_i^{\mathrm{par}}(f)\) indicate parameter-aware ordered recovery.

The package universally enforces \(A_i(f)\leq E_i(f)\) and:

\[
M_i^{\mathrm{par}}(f)
\leq M_i^{\mathrm{ord}}(f)
\leq M_i^{\mathrm{sig}}(f)
\leq E_i(f).
\]

The frozen release additionally validates
\(M_i^{\mathrm{sig}}(f)\leq A_i(f)\) in all 3,234 cells, producing the observed
chain:

\[
M^{\mathrm{par}}\preceq M^{\mathrm{ord}}
\preceq M^{\mathrm{sig}}\preceq A\preceq E.
\]

The package reports future \(M^{\mathrm{sig}}=1,A=0\) cells rather than
rejecting them universally because \(M^{\mathrm{sig}}\preceq A\) is an
empirical release invariant, not a theorem about every exporter.

## 2. Execution Rate

\[
\bar E(F;S)=
\frac{1}{N}
\sum_{f\in F}\sum_{i\in S}E_i(f).
\]

Execution establishes operational admissibility in the frozen evaluator. It
does not establish reference reconstruction or semantic correctness.

## 3. Quantum-Assembly Admissibility

\[
\bar A(F;S)=
\frac{1}{N}
\sum_{f\in F}\sum_{i\in S}A_i(f).
\]

Assembly admissibility requires \(E=1\) and successful serialization of the
selected circuit to OpenQASM 3 under the evaluator. It does not mean that the
emitted assembly was executed on a simulator or hardware backend.

## 4. Reference-Signature Rate

\[
\bar M^{\mathrm{sig}}(F;S)=
\frac{1}{N}
\sum_{f\in F}\sum_{i\in S}M_i^{\mathrm{sig}}(f).
\]

The frozen signature requires equality of:

- qubit count;
- classical-bit count; and
- complete evaluator-visible operation-type count map.

The count map records operation multiplicities by type. It is stronger than a
gate-vocabulary set. Scalar counted-operation equality follows from complete
count-map equality under the frozen convention and is retained as a separate
diagnostic rather than another joint conjunct.

## 5. Execution-Structure Gap

The pooled ES-Gap is:

\[
\Delta_{\mathrm{ES}}(F,S)=
\bar E(F;S)-\bar M^{\mathrm{sig}}(F;S).
\]

Because \(M^{\mathrm{sig}}\leq E\), the difference is also:

\[
\Delta_{\mathrm{ES}}(F,S)=
\frac{1}{N}
\sum_{f\in F}\sum_{i\in S}
\mathbf{1}\{E_i(f)=1,M_i^{\mathrm{sig}}(f)=0\}.
\]

It therefore counts an observed cell state rather than subtracting unrelated
leaderboard quantities.

The package reports:

- `es_gap_count`;
- `es_gap_rate`; and
- `executable_signature_disagreement_rate`.

## 6. Assembly-Structure Gap

The signature-level Assembly-Structure Gap (AS-Gap) is:

\[
\Delta_{\mathrm{AS}}^{\mathrm{sig}}(F,S)=
\bar A(F;S)-\bar M^{\mathrm{sig}}(F;S).
\]

The package reports:

- `assembly_count` and `assembly_rate`;
- `execution_to_assembly_attrition_count` and
  `execution_to_assembly_attrition_rate`;
- `as_gap_count` and `as_gap_rate`;
- `assembly_without_signature_count`;
- `signature_without_assembly_count`; and
- `as_gap_share_of_es_gap`.

On the frozen panel, \(M^{\mathrm{sig}}\preceq A\), so the AS-Gap is the rate
of \(A=1,M^{\mathrm{sig}}=0\) cells and its cell set is nested within the
ES-Gap cell set:

\[
\mathcal H_{\mathrm{AS}}\subseteq\mathcal H_{\mathrm{ES}},\qquad
\Delta_{\mathrm{ES}}^{\mathrm{sig}}
=(\bar E-\bar A)+\Delta_{\mathrm{AS}}^{\mathrm{sig}}.
\]

For future supplied data with an \(M^{\mathrm{sig}}=1,A=0\) cell, `as_gap_count`
remains the signed aggregate contrast \(A-M^{\mathrm{sig}}\), while the two
directional disagreement counts remain separately visible.

## 7. Conditional Executable Disagreement

For at least one executable cell:

\[
\mathrm{ERSD}(F,S)=
\frac{
\sum_{f\in F}\sum_{i\in S}
[E_i(f)-M_i^{\mathrm{sig}}(f)]
}{
\sum_{f\in F}\sum_{i\in S}E_i(f)
}
=
\frac{\Delta_{\mathrm{ES}}(F,S)}{\bar E(F;S)}.
\]

ERSD is the executable reference-signature disagreement rate. In package
output it is named `executable_signature_disagreement_rate`.

The denominator differs from the ES-Gap rate:

- ES-Gap rate divides by all model-prompt cells.
- ERSD divides only by executable cells.

## 8. Structural Hallucination And SHR

Let \(T_{\mathrm{id}}\) be the 150-prompt subset whose wording uniquely
specifies every frozen signature component. For \(i\in T_{\mathrm{id}}\):

\[
\mathrm{SH}_i(f)=
E_i(f)[1-M_i^{\mathrm{sig}}(f)].
\]

This cell state is called a structural hallucination. Its conditional
frequency among executable identifiable cells is:

\[
\mathrm{SHR}(F,T_{\mathrm{id}})=
\frac{
\sum_{f\in F}\sum_{i\in T_{\mathrm{id}}}\mathrm{SH}_i(f)
}{
\sum_{f\in F}\sum_{i\in T_{\mathrm{id}}}E_i(f)
}.
\]

On an identifiable prompt set, SHR and ERSD have the same arithmetic form.
The separate name marks the stronger attribution permitted by prompt
identifiability.

Do not call every \(E=1,M=0\) cell in the complete 154-prompt matrix a
structural hallucination. Four prompts are intentionally retained only in the
stress-inclusive primary analysis.

## 9. Ordered And Parameter-Aware Layers

The ordered layer requires equality of:

- circuit width;
- ordered operation names;
- quantum operands; and
- classical operands.

The parameter-aware layer additionally requires equality of the
evaluator-normalized ordered parameter-value sequence.

Their ES-Gaps use the same execution baseline:

\[
\Delta_{\mathrm{ES}}^{\mathrm{ord}}(F,S)=
\bar E(F;S)-\bar M^{\mathrm{ord}}(F;S),
\]

\[
\Delta_{\mathrm{ES}}^{\mathrm{par}}(F,S)=
\bar E(F;S)-\bar M^{\mathrm{par}}(F;S).
\]

Pointwise nesting guarantees:

\[
\Delta_{\mathrm{ES}}^{\mathrm{sig}}
\leq
\Delta_{\mathrm{ES}}^{\mathrm{ord}}
\leq
\Delta_{\mathrm{ES}}^{\mathrm{par}}.
\]

## 10. Frozen Primary Values

The complete frozen matrix has \(N=21\times154=3{,}234\) cells.

| Endpoint | Count | Denominator | Rate |
| --- | ---: | ---: | ---: |
| execution | 2,950 | 3,234 | 91.22% |
| assembly admissibility | 2,944 | 3,234 | 91.03% |
| signature recovery | 1,703 | 3,234 | 52.66% |
| execution-to-assembly attrition | 6 | 3,234 | 0.19 percentage points |
| AS-Gap | 1,241 | 3,234 | 38.37 percentage points |
| ES-Gap | 1,247 | 3,234 | 38.56 percentage points |
| executable disagreement | 1,247 | 2,950 | 42.27% |
| ordered recovery | 1,576 | 3,234 | 48.73% |
| parameter-aware recovery | 1,545 | 3,234 | 47.77% |

The stronger gaps are:

\[
\Delta_{\mathrm{ES}}^{\mathrm{ord}}
=\frac{2{,}950-1{,}576}{3{,}234}
=0.4249,
\]

\[
\Delta_{\mathrm{ES}}^{\mathrm{par}}
=\frac{2{,}950-1{,}545}{3{,}234}
=0.4344.
\]

Of the 1,703 signature passes, 127 fail exact ordered operation-and-operand
recovery. A further 31 ordered passes fail parameter-aware recovery.

The frozen decomposition is exact:

\[
\frac{1{,}247}{3{,}234}
=
\frac{6}{3{,}234}
+
\frac{1{,}241}{3{,}234}.
\]

The AS-Gap therefore accounts for \(1{,}241/1{,}247=99.52\%\) of the
signature-level ES-Gap.

## 11. Frozen Identifiable-Subset Values

The identifiable subset has \(21\times150=3{,}150\) cells.

| Endpoint | Count | Denominator | Rate |
| --- | ---: | ---: | ---: |
| execution | 2,890 | 3,150 | 91.75% |
| signature recovery | 1,703 | 3,150 | 54.06% |
| ES-Gap | 1,187 | 3,150 | 37.68 percentage points |
| structural-hallucination rate | 1,187 | 2,890 | 41.07% |

The execution and signature rates use the same 3,150-cell denominator. SHR
uses the 2,890 executable-cell denominator.

## 12. Missing Optional Endpoints

`evaluate` reports `ordered_count` or `parameter_count` as `null` when that
layer is not completely available across executable rows. It does not mix a
partial numerator with the full cell denominator.

Assembly fields are optional for backward-compatible candidate records, but
they must be present on every record or omitted from every record in one
summary. Execution and signature fields are always required.

## 13. Comparison Denominators

A rate difference is interpretable only after the prompt set has been aligned.
Default comparison uses all 154 frozen prompts. Explicit partial comparison
restricts frozen rows to the candidate's exact prompt IDs.

The comparison record stores:

- the complete prompt-ID list;
- its SHA-256 digest;
- candidate and frozen dimensions; and
- the identifiable exclusions.

These fields make the denominator auditable without relying on a plot or table
caption.

## 14. Interpretive Limits

A signature failure proves disagreement with at least one measured frozen
descriptor. It does not prove that the generated circuit is useless,
physically invalid, or semantically inequivalent.

A signature, ordered, or parameter-aware pass proves exact agreement under
that predicate. It does not prove unitary equivalence, global-phase
equivalence, measurement-distribution equivalence, or task-level semantic
correctness.

Semantic equivalence is a separate evaluation axis.
