import tempfile
import unittest
from unittest.mock import Mock

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

    def test_get_problem_setup_returns_inputs_and_outputs(self):
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

            inputs, outputs = client.getProblemSetup()

            self.assertEqual(inputs, ["x"])
            self.assertEqual(outputs, ["y"])
            env.requests.get.assert_called_once_with(
                "http://computer:8001/problem_setup/problem-1",
                headers={
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )

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


if __name__ == "__main__":
    unittest.main()
