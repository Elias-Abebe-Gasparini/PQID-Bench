# Isolated Evaluator Worker

This image supplies the frozen Qiskit runtime for executable replay. The
`pqid-bench replay` command mounts the release read-only, disables container
networking, drops Linux capabilities, enables `no-new-privileges`, and applies
CPU, memory, process, and timeout boundaries.

Restricted Python built-ins define evaluator admissibility; they are not the
security boundary. Docker isolation is mandatory for this command. API
credentials must never be mounted into the evaluator container.

The runtime is pinned to Python 3.13, Qiskit 2.1.1, Qiskit Aer 0.17.0, and
python-dateutil 2.9.0.post0. The explicit python-dateutil pin satisfies the
runtime import used by Qiskit Aer; the image build fails immediately if the
three Python packages cannot be imported together.
