import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, call

from _solverai_test_support import FakeResponse, json_response, solverai_test_environment


def build_solver_results_payload():
    return {
        "Number Of Results": 1,
        "Objective Variable Names": "['objective']",
        "Constraint Variable Names": "['constraint']",
        "Input Variable Names": "['x']",
        "Output Variable Names": "['y']",
        "X0": "[1.0]",
        "Y0": "[2.0]",
    }


class SolverAiClientComputeTests(unittest.TestCase):

    def test_get_problem_status_info_returns_ready_state(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(200, "ready")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            status_info = client.getProblemStatusInfo()

            self.assertEqual(status_info.http_status_code, 200)
            self.assertEqual(status_info.state, "READY")
            self.assertEqual(status_info.detail, "ready")
            self.assertTrue(status_info.is_ready)
            self.assertFalse(status_info.is_processing)
            self.assertFalse(status_info.is_error)
            self.assertFalse(status_info.is_updating)
            self.assertFalse(status_info.require_not_updating)
            self.assertEqual(status_info.raw_status_text, "ready")

    def test_get_problem_status_info_returns_processing_state(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(202, "setup in execution")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            status_info = client.getProblemStatusInfo()

            self.assertEqual(status_info.http_status_code, 202)
            self.assertEqual(status_info.state, "PROCESSING")
            self.assertTrue(status_info.is_processing)
            self.assertFalse(status_info.is_ready)

    def test_get_problem_status_info_returns_not_ready_state(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                "NOT_READY: setup required",
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            status_info = client.getProblemStatusInfo()

            self.assertEqual(status_info.http_status_code, 400)
            self.assertEqual(status_info.state, "NOT_READY")
            self.assertEqual(status_info.detail, "NOT_READY: setup required")
            self.assertFalse(status_info.is_ready)
            self.assertFalse(status_info.is_processing)
            self.assertFalse(status_info.is_error)

    def test_get_problem_status_info_returns_error_state(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                "ERROR: setup failed",
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            status_info = client.getProblemStatusInfo()

            self.assertEqual(status_info.http_status_code, 400)
            self.assertEqual(status_info.state, "ERROR")
            self.assertTrue(status_info.is_error)
            self.assertEqual(status_info.error_origin, "unknown")

    def test_get_problem_status_info_supports_require_not_updating(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(202, "updating")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            status_info = client.getProblemStatusInfo(require_not_updating=True)

            self.assertEqual(status_info.state, "UPDATING")
            self.assertTrue(status_info.is_updating)
            self.assertTrue(status_info.require_not_updating)
            env.requests.get.assert_called_once_with(
                "http://computer:8001/check_problem_status/problem-1",
                headers={
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
                params={"require_not_updating": "true"},
            )

    def test_get_problem_status_info_raises_on_malformed_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = FakeResponse(200, "not-json")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemStatusInfo()

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_get_problem_status_info_does_not_retry_on_draining_status_response(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                503,
                {"detail": "Draining"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemStatusInfo()

            self.assertIn("Draining", str(ctx.exception))
            self.assertEqual(env.requests.get.call_count, 1)

    def test_wait_for_problem_ready_returns_immediately_on_ready(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(200, "ready")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                status_info = client.waitForProblemReady()
            finally:
                module.sleep = original_sleep

            self.assertEqual(status_info.state, "READY")
            self.assertTrue(status_info.is_ready)
            mock_sleep.assert_not_called()

    def test_wait_for_problem_ready_polls_processing_until_ready(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(202, "setup in execution"),
                json_response(200, "ready"),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                status_info = client.waitForProblemReady(
                    poll_interval_seconds=2.5,
                )
            finally:
                module.sleep = original_sleep

            self.assertEqual(status_info.state, "READY")
            mock_sleep.assert_called_once_with(2.5)

    def test_wait_for_problem_ready_with_require_not_updating_polls_until_ready(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(202, "setup in execution"),
                json_response(202, "updating"),
                json_response(200, "ready"),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                status_info = client.waitForProblemReady(
                    require_not_updating=True,
                )
            finally:
                module.sleep = original_sleep

            self.assertEqual(status_info.state, "READY")
            self.assertTrue(status_info.require_not_updating)
            self.assertEqual(mock_sleep.call_args_list, [call(1.0), call(1.0)])
            self.assertEqual(
                env.requests.get.call_args_list,
                [
                    call(
                        "http://computer:8001/check_problem_status/problem-1",
                        headers={
                            "Authorization": "Token token",
                            "Content-Type": "application/json",
                        },
                        params={"require_not_updating": "true"},
                    ),
                    call(
                        "http://computer:8001/check_problem_status/problem-1",
                        headers={
                            "Authorization": "Token token",
                            "Content-Type": "application/json",
                        },
                        params={"require_not_updating": "true"},
                    ),
                    call(
                        "http://computer:8001/check_problem_status/problem-1",
                        headers={
                            "Authorization": "Token token",
                            "Content-Type": "application/json",
                        },
                        params={"require_not_updating": "true"},
                    ),
                ],
            )

    def test_wait_for_problem_ready_raises_runtime_error_on_not_ready(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                "NOT_READY: setup required",
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(RuntimeError) as ctx:
                    client.waitForProblemReady()
            finally:
                module.sleep = original_sleep

            self.assertIn("NOT_READY", str(ctx.exception))
            mock_sleep.assert_not_called()

    def test_wait_for_problem_ready_raises_runtime_error_on_error(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                "ERROR: setup failed",
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(RuntimeError) as ctx:
                    client.waitForProblemReady()
            finally:
                module.sleep = original_sleep

            self.assertIn("ERROR", str(ctx.exception))
            mock_sleep.assert_not_called()

    def test_wait_for_problem_ready_raises_timeout_error(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(202, "setup in execution"),
                json_response(202, "setup in execution"),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            original_monotonic = module.monotonic
            mock_sleep = Mock()
            mock_monotonic = Mock(side_effect=[0.0, 0.0, 0.75])
            module.sleep = mock_sleep
            module.monotonic = mock_monotonic

            try:
                with self.assertRaises(TimeoutError):
                    client.waitForProblemReady(max_wait_seconds=0.75)
            finally:
                module.sleep = original_sleep
                module.monotonic = original_monotonic

            mock_sleep.assert_called_once_with(0.75)

    def test_wait_for_problem_ready_does_not_poll_past_timeout_boundary(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(202, "setup in execution"),
                json_response(200, "ready"),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            original_monotonic = module.monotonic
            mock_sleep = Mock()
            mock_monotonic = Mock(side_effect=[0.0, 0.0, 0.75])
            module.sleep = mock_sleep
            module.monotonic = mock_monotonic

            try:
                with self.assertRaises(TimeoutError):
                    client.waitForProblemReady(max_wait_seconds=0.75)
            finally:
                module.sleep = original_sleep
                module.monotonic = original_monotonic

            mock_sleep.assert_called_once_with(0.75)
            self.assertEqual(env.requests.get.call_count, 1)

    def test_get_problem_status_returns_inputs_and_outputs(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                200,
                {"inputs": ["x"], "outputs": ["y"]},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            inputs, outputs = client.getProblemStatus()

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            env.requests.get.assert_called_once_with(
                "http://computer:8001/check_problem_status/problem-1",
                headers={
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )

    def test_get_problem_status_raises_on_malformed_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = FakeResponse(200, "not-json")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemStatus()

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_get_problem_status_raises_on_non_2xx_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                {"detail": "bad request"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemStatus()

            self.assertIn("bad request", str(ctx.exception))

    def test_get_problem_status_does_not_retry_on_draining_status_response(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                503,
                {"detail": "Draining"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemStatus()

            self.assertIn("Draining", str(ctx.exception))
            self.assertEqual(env.requests.get.call_count, 1)

    def test_get_inputs_outputs_returns_inputs_and_outputs(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                200,
                {"inputs": ["x"], "outputs": ["y"]},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            inputs, outputs = client.getInputsOutputs()

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            env.requests.get.assert_called_once_with(
                "http://computer:8001/problem_setup/problem-1",
                headers={
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )

    def test_get_problem_setup_returns_inputs_and_outputs(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            client.getInputsOutputs = Mock(return_value=(["x"], ["y"]))

            inputs, outputs = client.getProblemSetup()

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            client.getInputsOutputs.assert_called_once_with()

    def test_get_problem_setup_retries_after_draining_response(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                json_response(200, {"inputs": ["x"], "outputs": ["y"]}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.25)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                inputs, outputs = client.getProblemSetup()
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            mock_sleep.assert_called_once_with(60.0)
            mock_random.assert_not_called()

    def test_get_problem_setup_raises_on_malformed_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = FakeResponse(200, "not-json")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemSetup()

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_get_problem_setup_raises_on_non_2xx_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                400,
                {"detail": "bad request"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getProblemSetup()

            self.assertIn("bad request", str(ctx.exception))

    def test_get_inputs_outputs_preserves_non_drain_202_behavior(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.return_value = json_response(
                202,
                "setup in execution",
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            with self.assertRaises(Exception) as ctx:
                client.getInputsOutputs()

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_get_inputs_outputs_retries_after_draining_response(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                json_response(200, {"inputs": ["x"], "outputs": ["y"]}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.25)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                inputs, outputs = client.getInputsOutputs()
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            mock_sleep.assert_called_once_with(60.0)
            mock_random.assert_not_called()

    def test_get_inputs_outputs_honors_http_date_retry_after(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            env.requests.get.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "Thu, 01 Jan 2026 00:01:00 GMT"},
                ),
                json_response(200, {"inputs": ["x"], "outputs": ["y"]}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )

            class FixedDateTime:
                @staticmethod
                def now(tz=None):
                    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            original_sleep = module.sleep
            original_random = module.random.random
            original_datetime = module.datetime
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.25)
            module.sleep = mock_sleep
            module.random.random = mock_random
            module.datetime = FixedDateTime

            try:
                inputs, outputs = client.getInputsOutputs()
            finally:
                module.sleep = original_sleep
                module.random.random = original_random
                module.datetime = original_datetime

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            mock_sleep.assert_called_once_with(60.0)
            mock_random.assert_not_called()

    def test_run_solver_returns_results_on_successful_200(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = json_response(
                200,
                {"results": build_solver_results_payload()},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")

            results = client._runSolver(compute_input)

            self.assertEqual(results.getNumberOfResults(), 1)
            self.assertEqual(results.getInputVariableNames(), ["x"])
            self.assertEqual(results.getOutputVariableNames(), ["y"])

    def test_run_solver_raises_setup_in_execution_on_202(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            exceptions_module = env.module("SolverAiClientExceptions")
            env.requests.post.return_value = FakeResponse(202, "{}")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")

            with self.assertRaises(exceptions_module.SetupInExecutionException):
                client._runSolver(compute_input)

    def test_run_solver_raises_on_malformed_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = FakeResponse(200, "not-json")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")

            with self.assertRaises(Exception) as ctx:
                client._runSolver(compute_input)

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_run_solver_raises_on_non_2xx_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = json_response(
                400,
                {"detail": "solver failed"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")

            with self.assertRaises(Exception) as ctx:
                client._runSolver(compute_input)

            self.assertIn("solver failed", str(ctx.exception))

    def test_run_solver_retries_after_setup_in_execution(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                FakeResponse(202, "{}"),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(5)

    def test_run_solver_retries_after_draining_response_with_retry_after(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.25)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.0)
            mock_random.assert_not_called()

    def test_run_solver_uses_default_drain_retry_interval_with_jitter(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(503, {"detail": "Draining"}),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.25)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.25)
            mock_random.assert_called_once_with()

    def test_run_solver_falls_back_to_default_when_retry_after_is_nan(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "NaN"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.125)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.125)
            mock_random.assert_called_once_with()

    def test_run_solver_falls_back_to_default_when_retry_after_is_infinite(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "1e309"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.875)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.875)
            mock_random.assert_called_once_with()

    def test_run_solver_falls_back_to_default_when_retry_after_is_malformed(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "tomorrow-ish"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.75)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.75)
            mock_random.assert_called_once_with()

    def test_run_solver_ignores_retry_after_when_disabled(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "17"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
                honor_retry_after=False,
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.5)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(60.5)
            mock_random.assert_called_once_with()

    def test_run_solver_honors_fail_fast_drain_mode(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            exceptions_module = env.module("SolverAiClientExceptions")
            env.requests.post.return_value = json_response(
                503,
                {"detail": "Draining"},
                headers={"Retry-After": "60"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
                drain_max_retries=0,
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(
                    exceptions_module.SolverAiDrainingException
                ) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(ctx.exception.retry_after_seconds, 60)
            mock_sleep.assert_not_called()

    def test_run_solver_honors_zero_retry_after(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "0"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.5)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(0.0)
            mock_random.assert_not_called()

    def test_run_solver_clamps_negative_retry_after_to_zero(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "-5"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            original_random = module.random.random
            mock_sleep = Mock()
            mock_random = Mock(return_value=0.5)
            module.sleep = mock_sleep
            module.random.random = mock_random

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep
                module.random.random = original_random

            self.assertEqual(results.getNumberOfResults(), 1)
            mock_sleep.assert_called_once_with(0.0)
            mock_random.assert_not_called()

    def test_run_solver_raises_draining_exception_after_retry_budget_exhausted(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            exceptions_module = env.module("SolverAiClientExceptions")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(
                    exceptions_module.SolverAiDrainingException
                ) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(ctx.exception.retry_after_seconds, 60)
            mock_sleep.assert_called_once_with(60.0)

    def test_run_solver_does_not_retry_non_draining_503_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = json_response(
                503,
                {"detail": "Busy"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(Exception) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertIn("Busy", str(ctx.exception))
            mock_sleep.assert_not_called()

    def test_run_solver_does_not_retry_malformed_json_503_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = FakeResponse(503, "not-json")
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(Exception) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")
            mock_sleep.assert_not_called()

    def test_run_solver_does_not_retry_other_5xx_responses(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.return_value = json_response(
                500,
                {"detail": "Draining"},
            )
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(Exception) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertIn("Draining", str(ctx.exception))
            mock_sleep.assert_not_called()

    def test_run_solver_preserves_mixed_503_then_202_then_200_flow(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                FakeResponse(202, "{}"),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(results.getNumberOfResults(), 1)
            self.assertEqual(
                mock_sleep.call_args_list,
                [call(60.0), call(5)],
            )

    def test_run_solver_preserves_mixed_202_then_503_then_200_flow(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            env.requests.post.side_effect = [
                FakeResponse(202, "{}"),
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                json_response(200, {"results": build_solver_results_payload()}),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                results = client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(results.getNumberOfResults(), 1)
            self.assertEqual(
                mock_sleep.call_args_list,
                [call(5), call(60.0)],
            )

    def test_run_solver_enforces_cumulative_drain_wait_budget(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientCompute")
            input_module = env.module("SolverAiComputeInput")
            exceptions_module = env.module("SolverAiClientExceptions")
            env.requests.post.side_effect = [
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
                FakeResponse(202, "{}"),
                json_response(
                    503,
                    {"detail": "Draining"},
                    headers={"Retry-After": "60"},
                ),
            ]
            client = module.SolverAiClientCompute(
                "http://computer:8001",
                "token",
                "problem-1",
                drain_max_retries=2,
                drain_max_wait_seconds=61,
            )
            compute_input = input_module.SolverAiComputeInput("problem-1")
            original_sleep = module.sleep
            mock_sleep = Mock()
            module.sleep = mock_sleep

            try:
                with self.assertRaises(
                    exceptions_module.SolverAiDrainingException
                ) as ctx:
                    client.runSolver(compute_input)
            finally:
                module.sleep = original_sleep

            self.assertEqual(ctx.exception.retry_after_seconds, 60)
            self.assertEqual(
                mock_sleep.call_args_list,
                [call(60.0), call(5)],
            )


if __name__ == "__main__":
    unittest.main()
