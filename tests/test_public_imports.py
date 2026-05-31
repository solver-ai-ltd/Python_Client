import unittest

from _solverai_test_support import solverai_test_environment


class PublicImportTests(unittest.TestCase):

    def test_public_all_matches_documented_surface(self):
        with solverai_test_environment() as env:
            package = env.package
            expected_names = {
                "get_setup_data",
                "validate_token",
                "IdsDataManager",
                "SolverAiClientCompute",
                "SolverAiProblemStatusInfo",
                "SetupInExecutionException",
                "SolverAiClientSetup",
                "SolverAiComputeInput",
                "SolverAiComputeResults",
                "SolverAiResultsWriter",
            }

            self.assertEqual(set(package.__all__), expected_names)
            self.assertEqual(len(package.__all__), len(expected_names))

    def test_top_level_imports_exist_for_exported_names(self):
        with solverai_test_environment() as env:
            package = env.package

            for name in package.__all__:
                self.assertTrue(hasattr(package, name), name)


if __name__ == "__main__":
    unittest.main()
