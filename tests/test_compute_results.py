import unittest

from _solverai_test_support import solverai_test_environment


def build_results_payload():
    return {
        "Number Of Results": 2,
        "Objective Variable Names": "['objective']",
        "Constraint Variable Names": "['constraint']",
        "Input Variable Names": "['x', 'y']",
        "Output Variable Names": "['y']",
        "X0": "[1.0, 2.0]",
        "Y0": "[10.0]",
        "X1": "[3.0, 4.0]",
        "Y1": "[20.0]",
    }


class SolverAiComputeResultsTests(unittest.TestCase):

    def test_constructor_parses_minimal_valid_payload(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeResults")

            results = module.SolverAiComputeResults(build_results_payload())

            self.assertEqual(results.getNumberOfResults(), 2)
            self.assertEqual(results.getObjectiveVariableNames(), ["objective"])
            self.assertEqual(results.getConstraintVariableNames(), ["constraint"])
            self.assertEqual(results.getInputVariableNames(), ["x", "y"])
            self.assertEqual(results.getOutputVariableNames(), ["y"])
            self.assertEqual(results.getX(), [[1.0, 2.0], [3.0, 4.0]])
            self.assertEqual(results.getY(), [[10.0], [20.0]])

    def test_getters_return_parsed_values(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeResults")
            results = module.SolverAiComputeResults(build_results_payload())

            self.assertEqual(results.getObjectiveVariableNames()[0], "objective")
            self.assertEqual(results.getConstraintVariableNames()[0], "constraint")
            self.assertEqual(results.getInputVariableNames()[1], "y")
            self.assertEqual(results.getOutputVariableNames()[0], "y")

    def test_get_dataframe_combines_x_and_y(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeResults")
            results = module.SolverAiComputeResults(build_results_payload())

            dataframe = results.getDataFrame()

            self.assertEqual(dataframe.columns, ["x", "y"])
            self.assertEqual(dataframe.data, [[1.0, 10.0], [3.0, 20.0]])

    def test_get_dataframe_removes_duplicate_output_names_from_inputs(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeResults")
            results = module.SolverAiComputeResults(build_results_payload())

            dataframe = results.getDataFrame()

            self.assertNotIn("y", results.getInputVariableNames()[:1])
            self.assertEqual(dataframe.columns.count("y"), 1)


if __name__ == "__main__":
    unittest.main()
