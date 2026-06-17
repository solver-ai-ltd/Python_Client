import csv
import tempfile
import unittest

from _solverai_test_support import solverai_test_environment


def build_results_payload():
    return {
        "Number Of Results": 2,
        "Objective Variable Names": "['objective']",
        "Constraint Variable Names": "['constraint']",
        "Input Variable Names": "['x']",
        "Output Variable Names": "['y']",
        "X0": "[1.0]",
        "Y0": "[10.0]",
        "X1": "[3.0]",
        "Y1": "[20.0]",
    }


class SolverAiResultsWriterTests(unittest.TestCase):

    def test_write_emits_expected_csv_structure(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            results_module = env.module("SolverAiComputeResults")
            writer_module = env.module("SolverAiResultsWriter")
            results = results_module.SolverAiComputeResults(build_results_payload())
            output_path = f"{tmp_dir}/results.csv"

            writer_module.SolverAiResultsWriter(results).write(output_path)

            with open(output_path, newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

            self.assertEqual(rows[0], ["Number Of Results", "2"])
            self.assertEqual(rows[1], ["Objective Variable Names", "objective"])
            self.assertEqual(rows[2], ["Constraint Variable Names", "constraint"])
            self.assertEqual(rows[4], ["Inputs"])
            self.assertEqual(rows[5], ["#", "x"])
            self.assertEqual(rows[9], ["Outputs"])
            self.assertEqual(rows[10], ["#", "y"])

    def test_write_emits_x_and_y_rows_in_order(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            results_module = env.module("SolverAiComputeResults")
            writer_module = env.module("SolverAiResultsWriter")
            results = results_module.SolverAiComputeResults(build_results_payload())
            output_path = f"{tmp_dir}/results.csv"

            writer_module.SolverAiResultsWriter(results).write(output_path)

            with open(output_path, newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

            self.assertEqual(rows[6], ["X0", "1.0"])
            self.assertEqual(rows[7], ["X1", "3.0"])
            self.assertEqual(rows[11], ["Y0", "10.0"])
            self.assertEqual(rows[12], ["Y1", "20.0"])


if __name__ == "__main__":
    unittest.main()
