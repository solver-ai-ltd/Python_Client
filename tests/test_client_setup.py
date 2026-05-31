import tempfile
import unittest
from unittest.mock import Mock

from _solverai_test_support import FakeResponse, json_response, solverai_test_environment


class SolverAiClientSetupTests(unittest.TestCase):

    def test_process_response_returns_id_from_valid_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            result = client._SolverAiClientSetup__processResponse(
                json_response(201, {"id": "eq-1"})
            )

            self.assertEqual(result, "eq-1")

    def test_process_response_raises_on_malformed_json(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            with self.assertRaises(Exception) as ctx:
                client._SolverAiClientSetup__processResponse(
                    FakeResponse(201, "not-json")
                )

            self.assertEqual(str(ctx.exception), "Failed retrieving data.")

    def test_post_equation_builds_expected_json_payload(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.post.return_value = json_response(201, {"id": "eq-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            result = client.postEquation(
                "eq",
                "x+y",
                "x,y",
                "0",
            )

            self.assertEqual(result, "eq-1")
            _, kwargs = env.requests.post.call_args
            self.assertEqual(
                kwargs["headers"],
                {
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )
            self.assertEqual(
                kwargs["data"],
                (
                    '{"name": "eq", "equationString": "x+y", '
                    '"variablesString": "x,y", "vectorizationIndices": "0"}'
                ),
            )

    def test_patch_equation_includes_only_non_empty_fields(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.patch.return_value = json_response(200, {"id": "eq-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            client.patchEquation("eq-1", name="updated")

            _, kwargs = env.requests.patch.call_args
            self.assertEqual(kwargs["data"], '{"name": "updated"}')

    def test_post_code_uses_code_multipart_field(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("SolverAiClientSetup")
            env.requests.post.return_value = json_response(201, {"id": "code-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")
            code_path = f"{tmp_dir}/snippet.py"
            with open(code_path, "w", encoding="utf-8") as file:
                file.write("print('hello')\n")

            client.postCode("code", code_path, "x", "y")

            _, kwargs = env.requests.post.call_args
            self.assertEqual(kwargs["data"]["name"], "code")
            self.assertEqual(set(kwargs["files"].keys()), {"code"})

    def test_patch_code_without_file_path_uses_json_patch(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.patch.return_value = json_response(200, {"id": "code-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            client.patchCode("code-1", variablesStringOut="y")

            _, kwargs = env.requests.patch.call_args
            self.assertEqual(
                kwargs["headers"],
                {
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )
            self.assertEqual(kwargs["data"], '{"variablesStringOut": "y"}')

    def test_post_hard_data_accepts_dataframe_input(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.post.return_value = json_response(201, {"id": "hard-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")
            dataframe = env.pandas.DataFrame([[1, 2]], columns=["a", "b"])

            client.postHardData("dataset", dataframe)

            _, kwargs = env.requests.post.call_args
            uploaded = kwargs["files"]["csv"]
            self.assertEqual(uploaded[0], "data.csv")
            self.assertEqual(uploaded[1].getvalue(), "a,b\n1,2\n")
            self.assertEqual(uploaded[2], "text/csv")

    @unittest.expectedFailure
    def test_patch_hard_data_without_file_uses_metadata_only_patch(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.patch.return_value = json_response(200, {"id": "hard-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            client.patchHardData("hard-1", name="renamed")

            _, kwargs = env.requests.patch.call_args
            self.assertEqual(
                kwargs["headers"],
                {
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )
            self.assertEqual(kwargs["data"], '{"name": "renamed"}')

    def test_post_problem_builds_expected_problem_payload(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.post.return_value = json_response(201, {"id": "problem-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            client.postProblem(
                "problem",
                equationIds=["eq-1"],
                codeIds=["code-1"],
                hardIds=["hard-1"],
                softIds=["soft-1"],
            )

            _, kwargs = env.requests.post.call_args
            self.assertEqual(
                kwargs["data"],
                (
                    '{"name": "problem", "equations": ["eq-1"], '
                    '"codes": ["code-1"], "harddatas": ["hard-1"], '
                    '"softdatas": ["soft-1"], "tags": []}'
                ),
            )

    @unittest.expectedFailure
    def test_patch_soft_data_without_file_uses_metadata_only_patch(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.patch.return_value = json_response(200, {"id": "soft-1"})
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            client.patchSoftData("soft-1", variablesStringOut="y")

            _, kwargs = env.requests.patch.call_args
            self.assertEqual(
                kwargs["headers"],
                {
                    "Authorization": "Token token",
                    "Content-Type": "application/json",
                },
            )
            self.assertEqual(kwargs["data"], '{"variablesStringOut": "y"}')

    def test_flush_post_batch_returns_grouped_ids_in_submission_order(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup(
                "http://datamanagerapi:8000",
                "token",
                post_batch=True,
            )
            execute = Mock(side_effect=["eq-1", "code-1", "problem-1"])
            client._SolverAiClientSetup__execute_postpatch = execute

            client.postEquation("eq", "x+y", "x,y")
            client.postCode("code", "/tmp/unused.py", "x", "y")
            client.postProblem("problem")

            result = client.flush_post_batch()

            self.assertEqual(
                result,
                (["eq-1"], ["code-1"], [], [], "problem-1"),
            )

    def test_flush_post_batch_raises_on_empty_queue(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup(
                "http://datamanagerapi:8000",
                "token",
                post_batch=True,
            )

            with self.assertRaises(Exception) as ctx:
                client.flush_post_batch()

            self.assertEqual(str(ctx.exception), "Batch not setup")

    def test_flush_post_batch_rolls_back_when_a_request_fails(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup(
                "http://datamanagerapi:8000",
                "token",
                post_batch=True,
            )
            client._SolverAiClientSetup__execute_postpatch = Mock(
                side_effect=["eq-1", RuntimeError("boom")]
            )
            client.deleteAll = Mock()

            client.postEquation("eq", "x+y", "x,y")
            client.postProblem("problem")

            with self.assertRaises(Exception) as ctx:
                client.flush_post_batch()

            self.assertIn("Batch post completed with errors.", str(ctx.exception))
            client.deleteAll.assert_called_once_with(
                equationIds=["eq-1"],
                codeIds=[],
                hardIds=[],
                softIds=[],
                problemId=None,
            )

    def test_delete_all_deletes_problem_before_modules(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")
            calls = []

            def record_delete_ids(url_suffix, ids, all_errors):
                calls.append((url_suffix, list(ids)))

            client._SolverAiClientSetup__deleteIds = record_delete_ids

            client.deleteAll(
                equationIds=["eq-1"],
                codeIds=["code-1"],
                hardIds=["hard-1"],
                softIds=["soft-1"],
                problemId="problem-1",
            )

            self.assertEqual(
                calls,
                [
                    ("problems", ["problem-1"]),
                    ("equations", ["eq-1"]),
                    ("code", ["code-1"]),
                    ("hard-datas", ["hard-1"]),
                    ("soft-datas", ["soft-1"]),
                ],
            )

    def test_delete_all_raises_on_invalid_problem_id_type(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            with self.assertRaises(Exception):
                client.deleteAll(problemId=123)

    def test_get_problem_module_ids_by_name_returns_exact_match_ids(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.get.side_effect = [
                json_response(
                    200,
                    [
                        {"id": "problem-1", "name": "model-a"},
                        {"id": "problem-2", "name": "model"},
                    ],
                ),
                json_response(
                    200,
                    {
                        "equations": [{"id": "eq-1"}],
                        "codes": [{"id": "code-1"}],
                        "harddatas": [{"id": "hard-1"}],
                        "softdatas": [{"id": "soft-1"}],
                    },
                ),
            ]
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            result = client.getProblemModuleIdsByName("model")

            self.assertEqual(
                result,
                ("problem-2", ["eq-1"], ["code-1"], ["hard-1"], ["soft-1"]),
            )

    def test_get_problem_module_ids_by_name_raises_when_missing(self):
        with solverai_test_environment() as env:
            module = env.module("SolverAiClientSetup")
            env.requests.get.return_value = json_response(200, [])
            client = module.SolverAiClientSetup("http://datamanagerapi:8000", "token")

            with self.assertRaises(Exception) as ctx:
                client.getProblemModuleIdsByName("missing")

            self.assertIn("No problem found with name='missing'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
