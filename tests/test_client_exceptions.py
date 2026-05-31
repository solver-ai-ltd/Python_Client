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


if __name__ == "__main__":
    unittest.main()
