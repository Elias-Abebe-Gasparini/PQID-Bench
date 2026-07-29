from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pqid_bench.live import (
    LiveRunConfig,
    ProviderTransportError,
    plan_live_model_run,
    run_live_model,
)


def _write_release(root: Path, *, prompt_count: int = 2) -> list[dict[str, object]]:
    prompt_path = (
        root
        / "artifacts"
        / "test_split_154"
        / "pqid_bench_external_generation_prompts_154.jsonl"
    )
    prompt_path.parent.mkdir(parents=True)
    prompts = [
        {
            "prompt_id": f"pqid_bench_external_gen_{index:04d}",
            "row_id": f"row-{index}",
            "prompt": f"Prompt {index}",
            "messages": [
                {"role": "system", "content": "Return only code."},
                {"role": "user", "content": f"Build circuit {index}."},
            ],
            "target_metadata": {
                "gate_count": 9000 + index,
                "private_evaluator_only_marker": f"TARGET-{index}",
            },
        }
        for index in range(1, prompt_count + 1)
    ]
    prompt_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in prompts),
        encoding="utf-8",
    )
    relative = prompt_path.relative_to(root).as_posix()
    digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    (root / "ARTIFACT_MANIFEST.tsv").write_text(
        "path\tbytes\tsha256\n"
        f"{relative}\t{prompt_path.stat().st_size}\t{digest}\n",
        encoding="utf-8",
    )
    return prompts


def _success_payload(*, content: str = "qc = QuantumCircuit(1)") -> bytes:
    return json.dumps(
        {
            "id": "provider-request-1",
            "model": "resolved-model",
            "choices": [
                {
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 8},
        }
    ).encode("utf-8")


class LiveModelTests(unittest.TestCase):
    def _config(
        self,
        root: Path,
        output: Path,
        **overrides: object,
    ) -> LiveRunConfig:
        values: dict[str, object] = {
            "release_dir": root,
            "output_dir": output,
            "provider": "custom-test",
            "model": "requested-model",
            "base_url": "https://provider.example/v1",
            "api_key_env": "PQID_TEST_API_KEY",
            "acknowledge_prompt_export": True,
            "max_retries": 0,
        }
        values.update(overrides)
        return LiveRunConfig(**values)  # type: ignore[arg-type]

    def test_dry_run_plan_needs_no_credential_or_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root)
            config = self._config(
                root,
                root / "output",
                acknowledge_prompt_export=False,
            )
            with patch.dict(os.environ, {}, clear=True):
                plan = plan_live_model_run(config)
            self.assertFalse(plan["contacts_provider"])
            self.assertFalse(plan["target_metadata_exported"])
            self.assertEqual(plan["selected_prompts"], 2)

    def test_live_call_requires_explicit_prompt_export_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root)
            config = self._config(
                root,
                root / "output",
                acknowledge_prompt_export=False,
            )
            with self.assertRaisesRegex(ValueError, "acknowledgement"):
                run_live_model(config, transport=lambda *_: _success_payload())

    def test_rejects_prompt_id_path_traversal_before_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompts = _write_release(root, prompt_count=1)
            prompt_path = (
                root
                / "artifacts"
                / "test_split_154"
                / "pqid_bench_external_generation_prompts_154.jsonl"
            )
            prompts[0]["prompt_id"] = "../outside"
            prompt_path.write_text(
                json.dumps(prompts[0], sort_keys=True) + "\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            relative = prompt_path.relative_to(root).as_posix()
            (root / "ARTIFACT_MANIFEST.tsv").write_text(
                "path\tbytes\tsha256\n"
                f"{relative}\t{prompt_path.stat().st_size}\t{digest}\n",
                encoding="utf-8",
            )
            output = root / "output"
            with self.assertRaisesRegex(ValueError, "not safe"):
                plan_live_model_run(self._config(root, output))
            self.assertFalse(output.exists())

    def test_success_writes_trace_without_secret_or_target_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompts = _write_release(root)
            output = root / "output"
            observed_bodies: list[dict[str, object]] = []
            observed_headers: list[dict[str, str]] = []

            def transport(
                route: str,
                headers: object,
                body: bytes,
                timeout: float,
            ) -> bytes:
                self.assertEqual(route, "https://provider.example/v1/chat/completions")
                self.assertEqual(timeout, 120.0)
                observed_headers.append(dict(headers))  # type: ignore[arg-type]
                observed_bodies.append(json.loads(body))
                return _success_payload(content=f"result = {len(observed_bodies)}")

            secret = "test-secret-must-not-be-persisted"
            with patch.dict(os.environ, {"PQID_TEST_API_KEY": secret}, clear=True):
                result = run_live_model(
                    self._config(root, output),
                    transport=transport,
                )

            self.assertTrue(result.complete)
            self.assertEqual(result.successful_prompts, 2)
            self.assertEqual(len(observed_bodies), 2)
            self.assertEqual(
                observed_bodies[0]["messages"],
                prompts[0]["messages"],
            )
            self.assertNotIn("target_metadata", observed_bodies[0])
            self.assertEqual(
                observed_headers[0]["Authorization"],
                f"Bearer {secret}",
            )

            persisted = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in output.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(secret, persisted)
            self.assertNotIn("TARGET-1", persisted)
            self.assertNotIn("private_evaluator_only_marker", persisted)
            self.assertNotIn(str(root), persisted)
            self.assertTrue((output / "responses.jsonl").is_file())
            self.assertTrue((output / "provider-attempts.jsonl").is_file())
            self.assertTrue((output / "requests.jsonl").is_file())
            self.assertTrue((output / "run-manifest.json").is_file())
            self.assertTrue((output / "run-summary.json").is_file())
            response = json.loads(
                (output / "responses.jsonl").read_text(encoding="utf-8").splitlines()[0]
            )
            self.assertEqual(response["model"], "requested-model")
            self.assertEqual(response["resolved_model"], "resolved-model")
            manifest = json.loads(
                (output / "run-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["prompt_source"],
                (
                    "artifacts/test_split_154/"
                    "pqid_bench_external_generation_prompts_154.jsonl"
                ),
            )
            self.assertEqual(manifest["prompt_source_scope"], "release")
            summary = json.loads(
                (output / "run-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["output_dir"], ".")
            self.assertEqual(summary["response_file"], "responses.jsonl")

    def test_retryable_error_records_each_attempt_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root, prompt_count=1)
            output = root / "output"
            calls = 0
            delays: list[float] = []

            def transport(*_: object) -> bytes:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise ProviderTransportError(
                        "HTTP 429: rate limited",
                        retryable=True,
                        status_code=429,
                        raw_body=b'{"error":"rate limited"}',
                    )
                return _success_payload()

            with patch.dict(
                os.environ,
                {"PQID_TEST_API_KEY": "secret"},
                clear=True,
            ):
                result = run_live_model(
                    self._config(
                        root,
                        output,
                        max_retries=1,
                        retry_backoff_seconds=0.25,
                    ),
                    transport=transport,
                    sleep=delays.append,
                )

            self.assertTrue(result.complete)
            self.assertEqual(calls, 2)
            self.assertEqual(delays, [0.25])
            attempts = [
                json.loads(line)
                for line in (output / "provider-attempts.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual([row["status"] for row in attempts], ["error", "success"])
            self.assertTrue(attempts[1]["transport_affected"])
            response = json.loads(
                (output / "responses.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(response["attempt_count"], 2)
            self.assertTrue(response["transport_affected"])

    def test_resume_skips_completed_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root, prompt_count=2)
            output = root / "output"
            calls = 0

            def transport(*_: object) -> bytes:
                nonlocal calls
                calls += 1
                return _success_payload()

            with patch.dict(
                os.environ,
                {"PQID_TEST_API_KEY": "secret"},
                clear=True,
            ):
                first = run_live_model(
                    self._config(root, output, max_new=1),
                    transport=transport,
                )
                resumed = run_live_model(
                    self._config(root, output, resume=True),
                    transport=transport,
                )

            self.assertEqual(first.pending_prompts, 1)
            self.assertTrue(resumed.complete)
            self.assertEqual(resumed.attempted_this_invocation, 1)
            self.assertEqual(resumed.skipped_this_invocation, 1)
            self.assertEqual(calls, 2)

    def test_terminal_error_can_be_recovered_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root, prompt_count=1)
            output = root / "output"

            def failure(*_: object) -> bytes:
                raise ProviderTransportError(
                    "HTTP 400: invalid request",
                    retryable=False,
                    status_code=400,
                    raw_body=b'{"error":"invalid request"}',
                )

            with patch.dict(
                os.environ,
                {"PQID_TEST_API_KEY": "secret"},
                clear=True,
            ):
                failed = run_live_model(
                    self._config(root, output),
                    transport=failure,
                )
                recovered = run_live_model(
                    self._config(
                        root,
                        output,
                        resume=True,
                        retry_errors=True,
                    ),
                    transport=lambda *_: _success_payload(),
                )

            self.assertEqual(failed.error_prompts, 1)
            self.assertTrue(recovered.complete)
            attempts = [
                json.loads(line)
                for line in (output / "provider-attempts.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[-1]["status"], "success")

    def test_interrupted_attempt_requires_duplicate_draw_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root, prompt_count=1)
            output = root / "output"
            with patch.dict(
                os.environ,
                {"PQID_TEST_API_KEY": "secret"},
                clear=True,
            ):
                run_live_model(
                    self._config(root, output),
                    transport=lambda *_: _success_payload(),
                )
                record_path = (
                    output
                    / "records"
                    / "pqid_bench_external_gen_0001.json"
                )
                record = json.loads(record_path.read_text(encoding="utf-8"))
                record["response"] = None
                record["status"] = "in_flight"
                record["active_attempt"] = {
                    **record["attempts"][-1],
                    "attempt_id": "uncertain-attempt",
                    "attempt_index": 2,
                    "status": "in_flight",
                    "completed_at": None,
                }
                record_path.write_text(
                    json.dumps(record),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(ValueError, "uncertain in-flight"):
                    run_live_model(
                        self._config(root, output, resume=True),
                        transport=lambda *_: _success_payload(),
                    )
                recovered = run_live_model(
                    self._config(
                        root,
                        output,
                        resume=True,
                        retry_uncertain=True,
                    ),
                    transport=lambda *_: _success_payload(),
                )

            self.assertTrue(recovered.complete)
            attempts = [
                json.loads(line)
                for line in (output / "provider-attempts.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(
                [attempt["status"] for attempt in attempts],
                ["success", "uncertain_interrupted", "success"],
            )

    def test_rejects_insecure_route_and_persisted_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_release(root, prompt_count=1)
            with self.assertRaisesRegex(ValueError, "Plain HTTP"):
                plan_live_model_run(
                    self._config(
                        root,
                        root / "output-a",
                        base_url="http://provider.example/v1",
                    )
                )
            with self.assertRaisesRegex(ValueError, "credential-like"):
                plan_live_model_run(
                    self._config(
                        root,
                        root / "output-b",
                        extra_body={"nested": {"api_key": "do-not-store"}},
                    )
                )


if __name__ == "__main__":
    unittest.main()
