import json
import unittest

from _solverai_test_support import solverai_test_environment


class SolverAiComputeInputTests(unittest.TestCase):

    def test_constructor_sets_default_solver_setup(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")

            compute_input = module.SolverAiComputeInput("problem-1")

            self.assertEqual(
                compute_input.solverSetup,
                {
                    "includeLeastInfeasible": 0,
                    "solutionQuality": 1,
                },
            )
            self.assertFalse(compute_input.isDebug)

    def test_set_solver_setup_serializes_boolean_flags(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1")

            compute_input.setSolverSetup(
                includeLeastInfeasible=True,
                solutionQuality=3,
            )

            self.assertEqual(
                compute_input.solverSetup,
                {
                    "includeLeastInfeasible": 1,
                    "solutionQuality": 3,
                },
            )

    def test_add_input_stores_range_and_integer_flags(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1")

            compute_input.addInput("x", 1, 5, is_integer=True)

            self.assertEqual(
                compute_input.inputs["x"],
                {
                    "Min": 1,
                    "Max": 5,
                    "Constant": False,
                    "Integer": True,
                },
            )

    def test_add_input_auto_promotes_equal_min_max_to_constant(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1")

            compute_input.addInput("x", 7, 7)

            self.assertTrue(compute_input.inputs["x"]["Constant"])

    def test_add_constraint_serializes_enum_value(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1")

            compute_input.addConstraint(
                "temperature",
                module.CONSTRAINT.INSIDE_RANGE,
                18,
                24,
            )

            self.assertEqual(
                compute_input.constraints["temperature"],
                {
                    "Operation": "inside range",
                    "Value1": 18,
                    "Value2": 24,
                },
            )

    def test_add_objective_serializes_enum_value(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1")

            compute_input.addObjective("energy", module.OBJECTIVE.MINIMIZE)

            self.assertEqual(
                compute_input.objectives["energy"],
                {"Operation": "minimize"},
            )

    def test_get_json_returns_full_payload_shape(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiComputeInput")
            compute_input = module.SolverAiComputeInput("problem-1", isDebug=True)
            compute_input.setSolverSetup(True, 2)
            compute_input.addInput("x", 1, 5)
            compute_input.addConstraint(
                "temperature",
                module.CONSTRAINT.SMALLER_THAN,
                12,
            )
            compute_input.addObjective("energy", module.OBJECTIVE.MAXIMIZE)

            payload = json.loads(compute_input.getJson())

            self.assertEqual(payload["id"], "problem-1")
            self.assertEqual(
                payload["solverSetup"],
                {
                    "includeLeastInfeasible": 1,
                    "solutionQuality": 2,
                },
            )
            self.assertEqual(payload["inputs"]["x"]["Min"], 1)
            self.assertEqual(
                payload["constraints"]["temperature"]["Operation"],
                "smaller than",
            )
            self.assertEqual(
                payload["objectives"]["energy"]["Operation"],
                "maximize",
            )
            self.assertTrue(payload["isDebug"])


if __name__ == "__main__":
    unittest.main()
