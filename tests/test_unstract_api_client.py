import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from unstract_api_client import UnstractClientError, configuration, run_once


class Response:
    def __init__(self, status, body): self.status, self.body = status, json.dumps(body).encode()
    def read(self): return self.body
    def getcode(self): return self.status
    def __enter__(self): return self
    def __exit__(self, *args): return False


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.pdf = self.root / "sample.pdf"; self.pdf.write_bytes(b"%PDF synthetic")
    def tearDown(self): self.tmp.cleanup()
    def test_dotenv_loading_and_environment_precedence(self):
        env_file=self.root/".env"; env_file.write_text("UNSTRACT_API_URL=https://dotenv.example/api\nUNSTRACT_API_KEY=dotenv-key\n")
        self.assertEqual(configuration(self.root, {}), ("https://dotenv.example/api", "dotenv-key"))
        self.assertEqual(configuration(self.root, {"UNSTRACT_API_URL":"https://explicit.example/api","UNSTRACT_API_KEY":"explicit-key"}), ("https://explicit.example/api", "explicit-key"))
    def test_missing_env_missing_values_and_placeholders(self):
        self.assertRaises(UnstractClientError, configuration, self.root, {})
        (self.root/".env").write_text("UNSTRACT_API_URL=https://ok.example/api\n")
        self.assertRaises(UnstractClientError, configuration, self.root, {})
        (self.root/".env").write_text("UNSTRACT_API_URL=https://us-central.unstract.com/deployment/api/<your-org-id>/bank_statement_processing/\nUNSTRACT_API_KEY=REPLACE_WITH_YOUR_API_KEY\n")
        with self.assertRaises(UnstractClientError) as ctx: configuration(self.root, {})
        self.assertNotIn("REPLACE_WITH", str(ctx.exception))
    def test_sync_success_and_safe_output(self):
        calls=[]
        def opener(req, timeout): calls.append(req); return Response(200, {"result": {"transactions": []}})
        out=self.root/"out.json"; summary=run_once(self.pdf,out,api_url="https://example.test/deployment/api/project/",api_key="secret",opener=opener)
        self.assertEqual(summary["http_status"],200); self.assertEqual(json.loads(out.read_text())["result"]["transactions"],[]); self.assertIn("Bearer secret", calls[0].headers.values())
        with self.assertRaises(UnstractClientError): run_once(self.pdf,out,api_url="https://example.test",api_key="secret",opener=opener)
    def test_hitl_queue_is_optional_and_trimmed(self):
        calls=[]
        def opener(req, timeout): calls.append(req); return Response(200, {"status": "completed"})
        run_once(self.pdf, self.root/"default.json", api_url="https://example.test", api_key="secret", opener=opener)
        self.assertNotIn(b"hitl_queue_name", calls[-1].data)
        run_once(self.pdf, self.root/"hitl.json", api_url="https://example.test", api_key="secret", hitl_queue_name="  review-queue  ", opener=opener)
        self.assertEqual(calls[-1].data.count(b"name=\"hitl_queue_name\""), 1)
        self.assertIn(b"\r\nreview-queue\r\n", calls[-1].data)
        run_once(self.pdf, self.root/"blank.json", api_url="https://example.test", api_key="secret", hitl_queue_name="   ", opener=opener)
        self.assertNotIn(b"hitl_queue_name", calls[-1].data)
    def test_async_polling(self):
        responses=iter([Response(200,{"execution_id":"x"}),Response(200,{"execution_id":"x"}),Response(200,{"status":"completed","result":{}})])
        with patch("unstract_api_client.time.sleep"):
            summary=run_once(self.pdf,self.root/"out.json",api_url="https://example.test/api",api_key="secret",poll_interval=0,max_wait=1,opener=lambda req,timeout: next(responses))
        self.assertTrue(summary["polling_used"])
    def test_cli_help_contains_hitl_option(self):
        from unstract_api_client import main
        with patch("unstract_api_client.configuration", side_effect=UnstractClientError("stop")):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
    def test_malformed_response_and_timeout(self):
        class BadResponse(Response):
            def __init__(self): self.status=200; self.body=b"{"
        def malformed(req, timeout): return BadResponse()
        with self.assertRaises(UnstractClientError): run_once(self.pdf,self.root/"bad.json",api_url="https://example.test",api_key="secret",opener=malformed)
        def timeout(req, timeout): raise TimeoutError("timed out")
        with self.assertRaises(UnstractClientError): run_once(self.pdf,self.root/"timeout.json",api_url="https://example.test",api_key="secret",opener=timeout)
    def test_authentication_failure(self):
        def unauthorized(req, timeout): raise urllib.error.HTTPError(req.full_url, 401, "unauthorized", {}, io.BytesIO(b'{}'))
        with self.assertRaises(UnstractClientError): run_once(self.pdf,self.root/"auth.json",api_url="https://example.test",api_key="secret",opener=unauthorized)
    def test_unsuccessful_processing_is_preserved(self):
        out=self.root/"failed.json"; run_once(self.pdf,out,api_url="https://example.test",api_key="secret",opener=lambda req,timeout: Response(200,{"status":"failed","error":"private detail"})); self.assertEqual(json.loads(out.read_text())["status"],"failed")

if __name__ == "__main__": unittest.main()
