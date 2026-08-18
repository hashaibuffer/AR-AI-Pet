import json
import unittest
from unittest import mock

# ``unittest discover -s companion`` adds this directory to ``sys.path``, so
# the runtime module is imported directly rather than as a package member.
import companion as runtime


class FakeResponse:
    def __init__(self, payload: dict, session_id: str | None = None):
        self._body = json.dumps(payload).encode()
        self.headers = {"mcp-session-id": session_id} if session_id else {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._body


def responses():
    return [
        FakeResponse({"jsonrpc": "2.0", "id": 1, "result": {}}, "session-1"),
        FakeResponse({"jsonrpc": "2.0", "result": {}}),
        FakeResponse(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"content": [{"type": "text", "text": "{}"}]},
            }
        ),
    ]


class McpAuthenticationTest(unittest.TestCase):
    def test_mcp_token_is_sent_on_every_request(self) -> None:
        seen = []

        def open_request(request, timeout):
            seen.append((request, timeout))
            return responses_queue.pop(0)

        responses_queue = responses()
        with (
            mock.patch.object(runtime, "MCP_TOKEN", "device-secret"),
            mock.patch.object(runtime.urllib.request, "urlopen", side_effect=open_request),
        ):
            runtime.mcp_call("get_status", timeout=8)

        self.assertEqual(3, len(seen))
        self.assertTrue(
            all(
                request.get_header("Authorization") == "Bearer device-secret"
                for request, _ in seen
            )
        )

    def test_empty_mcp_token_preserves_unauthenticated_deployments(self) -> None:
        seen = []

        def open_request(request, timeout):
            seen.append((request, timeout))
            return responses_queue.pop(0)

        responses_queue = responses()
        with (
            mock.patch.object(runtime, "MCP_TOKEN", ""),
            mock.patch.object(runtime.urllib.request, "urlopen", side_effect=open_request),
        ):
            runtime.mcp_call("get_status", timeout=8)

        self.assertTrue(
            all(request.get_header("Authorization") is None for request, _ in seen)
        )


class SttLanguagePolicyTest(unittest.TestCase):
    def test_remote_off_language_falls_back_to_forced_local_path(self) -> None:
        response = FakeResponse({"text": "Xingengfu.", "language": "en"})
        with (
            mock.patch.object(runtime, "WHISPER_REMOTE_URL", "https://stt.invalid"),
            mock.patch.object(runtime, "STT_LANGUAGES", ["zh"]),
            mock.patch.object(runtime.urllib.request, "urlopen", return_value=response),
        ):
            self.assertIsNone(runtime.transcribe_remote(b"ogg"))

    def test_remote_chinese_locale_is_accepted(self) -> None:
        response = FakeResponse({"text": "今天", "language": "zh-CN"})
        with (
            mock.patch.object(runtime, "WHISPER_REMOTE_URL", "https://stt.invalid"),
            mock.patch.object(runtime, "STT_LANGUAGES", ["zh"]),
            mock.patch.object(runtime.urllib.request, "urlopen", return_value=response),
        ):
            self.assertEqual(runtime.transcribe_remote(b"ogg"), "今天")


if __name__ == "__main__":
    unittest.main()
