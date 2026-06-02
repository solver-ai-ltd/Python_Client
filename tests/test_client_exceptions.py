import unittest

from _solverai_test_support import solverai_test_environment


class ClientExceptionTests(unittest.TestCase):

    def test_setup_in_execution_exception_uses_default_message(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientExceptions")

            error = module.SetupInExecutionException()

            self.assertEqual(str(error), "Setup not complete retry later.")

    def test_setup_in_execution_exception_preserves_custom_message(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientExceptions")

            error = module.SetupInExecutionException("custom message")

            self.assertEqual(str(error), "custom message")

    def test_solver_ai_draining_exception_exposes_stable_fields(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientExceptions")

            error = module.SolverAiDrainingException(
                retry_after_seconds=60,
            )

            self.assertEqual(error.status_code, 503)
            self.assertEqual(error.detail, "Draining")
            self.assertEqual(error.retry_after_seconds, 60)
            self.assertIn("503 Draining", str(error))

    def test_solver_ai_draining_exception_preserves_custom_message(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientExceptions")

            error = module.SolverAiDrainingException(
                status_code=503,
                detail="Draining",
                retry_after_seconds=15,
                message="custom draining message",
            )

            self.assertEqual(str(error), "custom draining message")
            self.assertEqual(error.retry_after_seconds, 15)


if __name__ == "__main__":
    unittest.main()
