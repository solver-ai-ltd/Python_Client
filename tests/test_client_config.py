import tempfile
import unittest

from _solverai_test_support import solverai_test_environment, write_temp_text_file


class GetSetupDataTests(unittest.TestCase):

    def test_get_setup_data_parses_valid_setup_file(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("client_config")
            setup_path = write_temp_text_file(
                tmp_dir,
                "setup.txt",
                (
                    "token=test-token\n"
                    "datamanagerUrl=http://datamanagerapi:8000\n"
                    "computerUrl=http://computer:8001\n"
                ),
            )

            result = module.get_setup_data(str(setup_path))

            self.assertEqual(
                result,
                (
                    "test-token",
                    "http://datamanagerapi:8000",
                    "http://computer:8001",
                ),
            )

    def test_get_setup_data_ignores_comments_and_blank_lines(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("client_config")
            setup_path = write_temp_text_file(
                tmp_dir,
                "setup.txt",
                (
                    "\n"
                    "# comment\n"
                    "token=test-token\n"
                    "\n"
                    "datamanagerUrl=http://datamanagerapi:8000\n"
                    "computerUrl=http://computer:8001\n"
                ),
            )

            result = module.get_setup_data(str(setup_path))

            self.assertEqual(result[0], "test-token")
            self.assertEqual(result[1], "http://datamanagerapi:8000")
            self.assertEqual(result[2], "http://computer:8001")

    def test_get_setup_data_raises_when_required_keys_are_missing(self):
        with solverai_test_environment() as env, tempfile.TemporaryDirectory() as tmp_dir:
            module = env.module("client_config")
            setup_path = write_temp_text_file(
                tmp_dir,
                "setup.txt",
                "token=test-token\n",
            )

            with self.assertRaises(Exception) as ctx:
                module.get_setup_data(str(setup_path))

            message = str(ctx.exception)
            self.assertIn('"datamanagerUrl" parameter not found in setup', message)
            self.assertIn('"computerUrl" parameter not found in setup', message)


class ValidateTokenTests(unittest.TestCase):

    def test_validate_token_returns_true_for_200(self):
        with solverai_test_environment() as env:
            module = env.module("client_config")
            env.requests.get.return_value = type(
                "Response",
                (),
                {"status_code": 200},
            )()

            result = module.validate_token(
                "http://datamanagerapi:8000",
                "test-token",
            )

            self.assertTrue(result)
            env.requests.get.assert_called_once_with(
                "http://datamanagerapi:8000/api/data/validate-token/",
                headers={"Authorization": "Token test-token"},
                timeout=60,
            )

    def test_validate_token_returns_false_for_non_200(self):
        with solverai_test_environment() as env:
            module = env.module("client_config")
            env.requests.get.return_value = type(
                "Response",
                (),
                {"status_code": 401},
            )()

            result = module.validate_token(
                "http://datamanagerapi:8000",
                "bad-token",
            )

            self.assertFalse(result)

    def test_validate_token_wraps_transport_exceptions(self):
        with solverai_test_environment() as env:
            module = env.module("client_config")
            env.requests.get.side_effect = RuntimeError("boom")

            with self.assertRaises(Exception) as ctx:
                module.validate_token(
                    "http://datamanagerapi:8000",
                    "test-token",
                )

            self.assertEqual(str(ctx.exception), "Failed verifying token.")


if __name__ == "__main__":
    unittest.main()
