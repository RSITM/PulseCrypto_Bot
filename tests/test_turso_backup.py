"""Offline tests for optional Turso paper state backup."""
import unittest
from unittest.mock import patch, Mock

from turso_backup import pipeline_url, execute


class TursoBackupTests(unittest.TestCase):
    def test_endpoint_accepts_turso_libsql_url(self):
        self.assertEqual(
            pipeline_url("libsql://pulsecrypto-example.turso.io"),
            "https://pulsecrypto-example.turso.io/v2/pipeline")

    def test_endpoint_rejects_unexpected_hosts(self):
        for url in ("http://pulsecrypto-example.turso.io",
                    "libsql://evil.example.com",
                    "libsql://pulsecrypto-example.turso.io.evil.com",
                    "libsql://user@pulsecrypto-example.turso.io",
                    "libsql://pulsecrypto-example.turso.io/?token=x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                pipeline_url(url)

    @patch("turso_backup.requests.post")
    def test_parameterized_execute_uses_bearer_auth(self, post):
        response = Mock()
        response.json.return_value = {
            "results": [
                {"type": "ok", "response": {
                    "type": "execute", "result": {"rows": []}}},
                {"type": "ok", "response": {"type": "close"}},
            ]}
        post.return_value = response
        result = execute("libsql://pulsecrypto-example.turso.io",
                         "private-test-token",
                         "SELECT ? AS example", ("sample",),
                         want_rows=True)
        self.assertEqual(result, {"rows": []})
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer private-test-token")
        self.assertEqual(kwargs["json"]["requests"][0]["stmt"]["args"],
                         [{"type": "text", "value": "sample"}])
        self.assertTrue(kwargs["json"]["requests"][0]["stmt"]["want_rows"])

    @patch("turso_backup.requests.post")
    def test_sql_error_is_rejected_without_secrets_in_error(self, post):
        response = Mock()
        response.json.return_value = {"results": [
            {"type": "error", "error": {"message": "some private SQL error"}}]}
        post.return_value = response
        with self.assertRaisesRegex(RuntimeError, "Turso SQL statement failed") as error:
            execute("libsql://pulsecrypto-example.turso.io",
                    "private-test-token", "SELECT 1")
        self.assertNotIn("private-test-token", str(error.exception))


if __name__ == "__main__":
    unittest.main()
