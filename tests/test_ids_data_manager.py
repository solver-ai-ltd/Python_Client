import tempfile
import unittest

from _solverai_test_support import solverai_test_environment


class IdsDataManagerTests(unittest.TestCase):

    def test_store_in_memory_and_retrieve_round_trip(self):
        with solverai_test_environment() as env:
            module = env.module("IdsDataManager")
            manager = module.IdsDataManager("unused.json")

            manager.storeInMemory(
                ["eq-1"],
                ["code-1"],
                ["hard-1"],
                ["soft-1"],
                "problem-1",
            )

            self.assertEqual(
                manager.retrieveFromMemory(),
                (
                    ["eq-1"],
                    ["code-1"],
                    ["hard-1"],
                    ["soft-1"],
                    "problem-1",
                ),
            )

    def test_write_and_read_round_trip_through_file(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("IdsDataManager")
            manager = module.IdsDataManager(f"{tmp_dir}/ids.json")

            manager.write(
                ["eq-1"],
                ["code-1"],
                ["hard-1"],
                ["soft-1"],
                "problem-1",
            )

            self.assertEqual(
                manager.read(),
                (
                    ["eq-1"],
                    ["code-1"],
                    ["hard-1"],
                    ["soft-1"],
                    "problem-1",
                ),
            )

    def test_file_exists_reports_before_and_after_write(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("IdsDataManager")
            manager = module.IdsDataManager(f"{tmp_dir}/ids.json")

            self.assertFalse(manager.fileExists())
            manager.write([], [], [], [], "problem-1")
            self.assertTrue(manager.fileExists())

    def test_read_problem_id_returns_only_stored_problem_id(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("IdsDataManager")
            manager = module.IdsDataManager(f"{tmp_dir}/ids.json")
            manager.write([], [], [], [], "problem-1")

            self.assertEqual(manager.readProblemId(), "problem-1")

    def test_remove_file_deletes_the_file(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("IdsDataManager")
            manager = module.IdsDataManager(f"{tmp_dir}/ids.json")
            manager.write([], [], [], [], "problem-1")

            manager.removeFile()

            self.assertFalse(manager.fileExists())


if __name__ == "__main__":
    unittest.main()
