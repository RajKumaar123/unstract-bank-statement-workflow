"""Small stdlib-only client for one controlled Unstract deployment request."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_TIMEOUT = 300
PLACEHOLDERS = {"", "REPLACE_WITH_YOUR_API_KEY", "REPLACE_WITH_API_KEY"}


class UnstractClientError(RuntimeError):
    pass


def load_dotenv(path: Path, environ: dict[str, str] | None = None) -> dict[str, str]:
    """Load simple KEY=VALUE entries without overriding explicit environment values."""
    target = os.environ if environ is None else environ
    if not path.is_file():
        return target
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key and key not in target:
            target[key] = value.strip('"\'')
    return target


def configuration(repo_root: Path | None = None, environ: dict[str, str] | None = None) -> tuple[str, str]:
    """Resolve endpoint and key from explicit env first, then repository-root .env."""
    values = dict(os.environ if environ is None else environ)
    root = repo_root or Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env", values)
    url, key = values.get("UNSTRACT_API_URL", "").strip(), values.get("UNSTRACT_API_KEY", "").strip()
    if not url or not key or key in PLACEHOLDERS or "<your-org-id>" in url:
        raise UnstractClientError("Unstract API configuration is missing or still uses placeholders")
    return url, key


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_body(response) -> Any:
    try:
        return json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UnstractClientError("Unstract returned a non-JSON response") from exc


def _request(url: str, *, method: str, headers: dict[str, str], body: bytes | None, timeout: float, opener: Callable = urllib.request.urlopen) -> tuple[int, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener(request, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            return status, _json_body(response)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read(512).decode("utf-8", "replace")
        except Exception:
            pass
        raise UnstractClientError(f"Unstract HTTP error {exc.code}: {detail[:200]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UnstractClientError(f"Unstract request failed: {exc}") from exc


def _multipart(pdf: Path, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----codex-unstract-boundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()])
    chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="files"; filename="{pdf.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode(), pdf.read_bytes(), f"\r\n--{boundary}--\r\n".encode()])
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _execution_id(body: Any) -> str | None:
    return body.get("execution_id") if isinstance(body, dict) and isinstance(body.get("execution_id"), str) else None


def run_once(pdf_path: Path, output_path: Path, *, api_url: str, api_key: str, hitl_queue_name: str | None = None, request_timeout: float = DEFAULT_TIMEOUT, poll_interval: float = 2.0, max_wait: float = 300.0, opener: Callable = urllib.request.urlopen) -> dict[str, Any]:
    if output_path.exists():
        raise UnstractClientError(f"Refusing to overwrite existing output: {output_path}")
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise UnstractClientError("Input must be an existing PDF file")
    if not api_key:
        raise UnstractClientError("API key is empty")
    started = _utc_now()
    headers = {"Authorization": f"Bearer {api_key}"}
    fields = {"timeout": str(DEFAULT_TIMEOUT), "include_metadata": "False"}
    if hitl_queue_name is not None and hitl_queue_name.strip():
        fields["hitl_queue_name"] = hitl_queue_name.strip()
    body, content_type = _multipart(pdf_path, fields)
    headers["Content-Type"] = content_type
    status, response = _request(api_url, method="POST", headers=headers, body=body, timeout=request_timeout, opener=opener)
    final = response
    execution_id = _execution_id(response)
    if execution_id:
        deadline = time.monotonic() + max_wait
        status_url = api_url + "?" + urllib.parse.urlencode({"execution_id": execution_id, "include_metadata": "False"})
        attempts = 0
        while time.monotonic() < deadline and attempts < max(1, int(max_wait / max(poll_interval, 0.1))):
            time.sleep(poll_interval); attempts += 1
            status, final = _request(status_url, method="GET", headers={"Authorization": f"Bearer {api_key}"}, body=None, timeout=request_timeout, opener=opener)
            # No status fields are interpreted: polling ends only when the service
            # stops returning an execution id, or the bounded wait is exhausted.
            if not _execution_id(final):
                break
        else:
            raise UnstractClientError("Unstract processing did not complete within the configured polling bound")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    return {"input_filename": pdf_path.name, "started_at": started, "completed_at": _utc_now(), "http_status": status, "execution_id_present": bool(execution_id), "polling_used": bool(execution_id), "output_path": str(output_path)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--max-wait", type=float, default=300.0)
    parser.add_argument("--hitl-queue-name")
    args = parser.parse_args(argv)
    try:
        api_url, api_key = configuration()
        summary = run_once(args.pdf, args.output, api_url=api_url, api_key=api_key, hitl_queue_name=args.hitl_queue_name, poll_interval=args.poll_interval, max_wait=args.max_wait)
        print(json.dumps({"status": "success", "http_status": summary["http_status"], "output_path": str(args.output), "polling_used": summary["polling_used"]}))
        return 0
    except (KeyError, UnstractClientError) as exc:
        print(f"unstract client error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
